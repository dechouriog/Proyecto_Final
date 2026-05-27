"""
Aplicación web Flask para registrar usuarios interesados en estudiar
una carrera de pregrado en la universidad.

Esta instancia tiene el idioma FIJO en inglés (Web Server 1 según consigna).
La instancia hermana (`aplicacion-web-espanol`) tiene el mismo código pero
con los textos en español. No se permite cambiar el idioma desde la UI,
es por ello que el idioma se fija a nivel de variable de entorno.

La aplicación expone:
    GET  /         -> formulario de registro
    POST /         -> procesa el formulario y guarda en BD
    GET  /salud    -> healthcheck para el balanceador
"""

import logging
import os
from datetime import datetime

from flask import Flask, render_template, request

from src.conexion_base_datos import RepositorioRegistros

# ---------------------------------------------------------------------------
# Configuración general de la app
# ---------------------------------------------------------------------------

# Carreras válidas según consigna del proyecto.
# Mantener sincronizado con el CHECK de la BD.
CARRERAS_VALIDAS = ("Medicina", "Ingenieria", "Abogacia", "Licenciatura")

# Las comunas son 1-10 según la consigna ("la ciudad tiene 10 comunas")
COMUNAS_VALIDAS = tuple(range(1, 11))

# Identificador del servidor (se lee de variable de entorno para diferenciar
# las dos instancias y demostrar visualmente que el round robin funciona).
IDENTIFICADOR_SERVIDOR = os.getenv("IDENTIFICADOR_SERVIDOR", "Web Server (sin id)")

# Idioma fijo de esta instancia ("en" o "es")
IDIOMA_APP = os.getenv("IDIOMA_APP", "en")

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inicialización Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Conexión a la base de datos: se inicializa perezosamente en cada petición
# para evitar problemas si MySQL aún no está listo cuando arranca la app.
repositorio = RepositorioRegistros()


# ===========================================================================
# Rutas
# ===========================================================================

@app.route("/", methods=["GET", "POST"])
def ruta_formulario_registro():
    """Muestra y procesa el formulario de registro."""

    mensaje_resultado = None
    fue_exitoso = False

    if request.method == "POST":
        # --- Extracción de campos del formulario --------------------------
        nombre_completo = (request.form.get("nombre_completo") or "").strip()
        numero_comuna_str = (request.form.get("numero_comuna") or "").strip()
        carrera_interes = (request.form.get("carrera_interes") or "").strip()

        # --- Validaciones -------------------------------------------------
        errores = _validar_datos_formulario(
            nombre_completo, numero_comuna_str, carrera_interes
        )

        if errores:
            mensaje_resultado = _construir_mensaje_error(errores)
            log.warning("Formulario inválido: %s", errores)
        else:
            # Conversión segura: ya validamos arriba
            numero_comuna = int(numero_comuna_str)

            try:
                repositorio.guardar_registro(
                    nombre_completo=nombre_completo,
                    numero_comuna=numero_comuna,
                    carrera_interes=carrera_interes,
                    fecha_ingreso=datetime.now(),
                    servidor_origen=IDENTIFICADOR_SERVIDOR,
                )
                fue_exitoso = True
                mensaje_resultado = _texto_exito()
                log.info(
                    "Registro guardado: nombre=%s comuna=%s carrera=%s",
                    nombre_completo, numero_comuna, carrera_interes
                )
            except Exception as error:  # noqa: BLE001 (queremos atrapar cualquier fallo de BD)
                log.error("Error guardando registro: %s", error)
                mensaje_resultado = _texto_error_servidor()

    # Renderizamos el template con los datos necesarios
    return render_template(
        "formulario.html",
        textos=_obtener_textos_interfaz(),
        comunas=COMUNAS_VALIDAS,
        carreras=CARRERAS_VALIDAS,
        mensaje_resultado=mensaje_resultado,
        fue_exitoso=fue_exitoso,
        identificador_servidor=IDENTIFICADOR_SERVIDOR,
    )


@app.route("/salud", methods=["GET"])
def ruta_health_check():
    """Endpoint simple para que NGINX (o monitoreo) verifique que la app vive."""
    return {"estado": "ok", "servidor": IDENTIFICADOR_SERVIDOR}, 200


# ===========================================================================
# Funciones auxiliares
# ===========================================================================

def _validar_datos_formulario(nombre, comuna_str, carrera):
    """Devuelve lista de errores. Lista vacía = todo OK."""
    errores = []

    if not nombre or len(nombre) < 2:
        errores.append("nombre_invalido")
    if len(nombre) > 150:
        errores.append("nombre_demasiado_largo")

    try:
        comuna = int(comuna_str)
        if comuna not in COMUNAS_VALIDAS:
            errores.append("comuna_invalida")
    except (ValueError, TypeError):
        errores.append("comuna_invalida")

    if carrera not in CARRERAS_VALIDAS:
        errores.append("carrera_invalida")

    return errores


def _obtener_textos_interfaz():
    """
    Devuelve el diccionario de textos según el idioma fijo de la instancia.
    Centralizamos aquí para que sea fácil mantener la otra instancia (español)
    en sincronía: ambas comparten el mismo template y solo cambian los textos.
    """
    textos_ingles = {
        "titulo_pagina": "Pregraduate Programs Registration",
        "titulo_formulario": "Tell us about your interest",
        "subtitulo": "Universidad EAFIT - Pregraduate Registration",
        "etiqueta_nombre": "Full name",
        "etiqueta_comuna": "Comuna (1 to 10)",
        "etiqueta_carrera": "Program of interest",
        "boton_enviar": "Submit registration",
        "comuna_placeholder": "Select your comuna",
        "carrera_placeholder": "Select a program",
        "pie_servidor": "Served by",
        "carreras_traducidas": {
            "Medicina": "Medicine",
            "Ingenieria": "Engineering",
            "Abogacia": "Law",
            "Licenciatura": "Teaching Degree",
        },
    }
    return textos_ingles


def _texto_exito():
    return "Registration saved successfully. Thank you!"


def _texto_error_servidor():
    return "There was an internal error. Please try again later."


def _construir_mensaje_error(errores):
    mapa_errores = {
        "nombre_invalido": "Please enter a valid name (minimum 2 characters).",
        "nombre_demasiado_largo": "Name is too long (maximum 150 characters).",
        "comuna_invalida": "Please select a comuna between 1 and 10.",
        "carrera_invalida": "Please select a valid program.",
    }
    mensajes = [mapa_errores.get(err, err) for err in errores]
    return " ".join(mensajes)
