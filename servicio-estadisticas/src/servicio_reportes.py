"""
Servicio de estadísticas.

Expone un endpoint HTTP que, al ser invocado por el administrador,
consulta la base de datos, genera dos gráficas (registros por comuna y
registros por carrera y comuna) y las envía por correo al destinatario
configurado en variables de entorno.

Endpoints:
    GET  /                       -> página simple con botón para disparar el envío
    POST /enviar-reporte         -> genera y envía el reporte
    GET  /salud                  -> healthcheck
"""

import logging
from datetime import datetime

from flask import Flask, jsonify, render_template_string, request

from src.consulta_estadisticas import obtener_estadisticas_agregadas
from src.generador_graficas import generar_imagenes_graficas
from src.envio_correo import enviar_correo_con_reporte

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)


# ===========================================================================
# Página simple con botón para disparar el envío
# ===========================================================================

PAGINA_ADMIN_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Panel de Estadísticas</title>
<style>
  body { font-family: system-ui, sans-serif; background: #f4f6f9;
         display: flex; align-items: center; justify-content: center;
         min-height: 100vh; margin: 0; padding: 20px; }
  .tarjeta { background: white; padding: 40px; border-radius: 12px;
             box-shadow: 0 4px 20px rgba(0,0,0,0.08); max-width: 480px;
             width: 100%; }
  h1 { color: #003366; margin-top: 0; }
  p { color: #555; line-height: 1.5; }
  button { background: #003366; color: white; border: none;
           padding: 14px 24px; font-size: 1rem; border-radius: 8px;
           cursor: pointer; width: 100%; font-weight: 600; }
  button:hover { background: #002244; }
  button:disabled { background: #999; cursor: not-allowed; }
  .resultado { margin-top: 20px; padding: 14px; border-radius: 8px;
               display: none; }
  .resultado.ok    { background: #e6f4ec; color: #1f7a3a; display: block; }
  .resultado.error { background: #fdecea; color: #b00020; display: block; }
</style>
</head>
<body>
  <div class="tarjeta">
    <h1>Panel de Estadísticas</h1>
    <p>
      Al presionar el botón se generarán las gráficas con los registros
      acumulados y se enviarán por correo al administrador del sistema.
    </p>
    <button id="boton-enviar" onclick="dispararEnvio()">
      Enviar reporte por correo
    </button>
    <div id="resultado" class="resultado"></div>
  </div>

<script>
async function dispararEnvio() {
    const boton = document.getElementById('boton-enviar');
    const cajaResultado = document.getElementById('resultado');
    boton.disabled = true;
    boton.textContent = 'Enviando...';
    cajaResultado.className = 'resultado';
    cajaResultado.textContent = '';

    try {
        const respuesta = await fetch('/enviar-reporte', { method: 'POST' });
        const datos = await respuesta.json();
        if (respuesta.ok) {
            cajaResultado.className = 'resultado ok';
            cajaResultado.textContent = datos.mensaje || 'Reporte enviado.';
        } else {
            cajaResultado.className = 'resultado error';
            cajaResultado.textContent = datos.mensaje || 'Error al enviar.';
        }
    } catch (err) {
        cajaResultado.className = 'resultado error';
        cajaResultado.textContent = 'Error de red: ' + err.message;
    } finally {
        boton.disabled = false;
        boton.textContent = 'Enviar reporte por correo';
    }
}
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def ruta_panel_administrador():
    """Página simple con un botón para disparar el envío."""
    return render_template_string(PAGINA_ADMIN_HTML)


@app.route("/enviar-reporte", methods=["POST"])
def ruta_enviar_reporte():
    """
    Pipeline completo:
      1. Consultar estadísticas agregadas desde BD.
      2. Generar las gráficas (PNG en memoria).
      3. Enviar el correo con las gráficas embebidas como adjuntos inline.
    """
    log.info("Solicitud de envío de reporte recibida")

    try:
        # 1. Consultar BD
        estadisticas = obtener_estadisticas_agregadas()
        log.info("Estadísticas obtenidas: %d registros totales", estadisticas["total_registros"])

        if estadisticas["total_registros"] == 0:
            return jsonify({
                "estado": "advertencia",
                "mensaje": "No hay registros aún en la base de datos.",
            }), 200

        # 2. Generar gráficas
        graficas = generar_imagenes_graficas(estadisticas)
        log.info("Gráficas generadas correctamente")

        # 3. Enviar correo
        enviar_correo_con_reporte(
            estadisticas=estadisticas,
            graficas_png=graficas,
            fecha_generacion=datetime.now(),
        )
        log.info("Correo enviado correctamente")

        return jsonify({
            "estado": "exito",
            "mensaje": "Reporte enviado correctamente al administrador.",
        }), 200

    except Exception as error:  # noqa: BLE001
        log.exception("Error generando o enviando el reporte: %s", error)
        return jsonify({
            "estado": "error",
            "mensaje": f"Error al enviar el reporte: {error}",
        }), 500


@app.route("/salud", methods=["GET"])
def ruta_health_check():
    return {"estado": "ok", "servicio": "estadisticas"}, 200
