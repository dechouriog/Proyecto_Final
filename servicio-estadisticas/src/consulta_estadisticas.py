"""
Capa de consulta a la BD para el servicio de estadísticas.

Devuelve un diccionario con todos los agregados que el reporte necesita.
"""

import logging
import os

import mysql.connector

log = logging.getLogger(__name__)


def _abrir_conexion():
    """Abre una conexión a MySQL leyendo la config de variables de entorno."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "base-de-datos"),
        port=int(os.getenv("MYSQL_PUERTO", "3306")),
        database=os.getenv("MYSQL_NOMBRE_BD", "registros_eafit"),
        user=os.getenv("MYSQL_USUARIO", "usuario_app"),
        password=os.getenv("MYSQL_PASSWORD_USUARIO", ""),
        charset="utf8mb4",
    )


def obtener_estadisticas_agregadas() -> dict:
    """
    Devuelve un diccionario con:
        - total_registros:           entero
        - conteo_por_comuna:         {numero_comuna -> cantidad}
        - conteo_por_carrera:        {nombre_carrera -> cantidad}
        - conteo_comuna_carrera:     {comuna -> {carrera -> cantidad}}
    """
    conexion = None
    cursor = None
    try:
        conexion = _abrir_conexion()
        # Usamos cursor con resultados como diccionarios para mayor legibilidad
        cursor = conexion.cursor(dictionary=True)

        # --- Total ---
        cursor.execute("SELECT COUNT(*) AS total FROM registros_interesados")
        total = cursor.fetchone()["total"]

        # --- Registros por comuna ---
        cursor.execute("""
            SELECT numero_comuna, COUNT(*) AS cantidad
            FROM registros_interesados
            GROUP BY numero_comuna
            ORDER BY numero_comuna
        """)
        conteo_por_comuna = {fila["numero_comuna"]: fila["cantidad"]
                              for fila in cursor.fetchall()}

        # --- Registros por carrera ---
        cursor.execute("""
            SELECT carrera_interes, COUNT(*) AS cantidad
            FROM registros_interesados
            GROUP BY carrera_interes
            ORDER BY carrera_interes
        """)
        conteo_por_carrera = {fila["carrera_interes"]: fila["cantidad"]
                               for fila in cursor.fetchall()}

        # --- Registros por comuna y carrera (para gráfica apilada) ---
        cursor.execute("""
            SELECT numero_comuna, carrera_interes, COUNT(*) AS cantidad
            FROM registros_interesados
            GROUP BY numero_comuna, carrera_interes
            ORDER BY numero_comuna, carrera_interes
        """)
        conteo_comuna_carrera = {}
        for fila in cursor.fetchall():
            comuna = fila["numero_comuna"]
            carrera = fila["carrera_interes"]
            cantidad = fila["cantidad"]
            if comuna not in conteo_comuna_carrera:
                conteo_comuna_carrera[comuna] = {}
            conteo_comuna_carrera[comuna][carrera] = cantidad

        return {
            "total_registros": total,
            "conteo_por_comuna": conteo_por_comuna,
            "conteo_por_carrera": conteo_por_carrera,
            "conteo_comuna_carrera": conteo_comuna_carrera,
        }

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
