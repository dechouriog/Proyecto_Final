"""
Módulo de acceso a la base de datos MySQL.

Se hace una conexión nueva por petición (es lo más simple y seguro para
una app de baja carga como ésta). Para producción de alto tráfico convendría
usar un pool de conexiones, pero para los volúmenes de esta práctica no
hace falta complicarlo.
"""

import logging
import os

import mysql.connector
from mysql.connector import Error as ErrorMySQL

log = logging.getLogger(__name__)


class RepositorioRegistros:
    """Capa de acceso a datos para la tabla `registros_interesados`."""

    def __init__(self):
        # Tomamos la configuración de variables de entorno inyectadas por Docker
        self._configuracion_conexion = {
            "host":     os.getenv("MYSQL_HOST", "base-de-datos"),
            "port":     int(os.getenv("MYSQL_PUERTO", "3306")),
            "database": os.getenv("MYSQL_NOMBRE_BD", "registros_eafit"),
            "user":     os.getenv("MYSQL_USUARIO", "usuario_app"),
            "password": os.getenv("MYSQL_PASSWORD_USUARIO", ""),
            "charset":  "utf8mb4",
        }

    def _abrir_conexion(self):
        """Abre una conexión a MySQL. Lanza ErrorMySQL si falla."""
        return mysql.connector.connect(**self._configuracion_conexion)

    def guardar_registro(
        self,
        nombre_completo: str,
        numero_comuna: int,
        carrera_interes: str,
        fecha_ingreso,
        servidor_origen: str,
    ) -> int:
        """
        Inserta un nuevo registro y devuelve el id generado.

        Usa parámetros preparados para evitar SQL injection.
        """
        sentencia_sql = """
            INSERT INTO registros_interesados
                (nombre_completo, numero_comuna, carrera_interes, fecha_ingreso, servidor_origen)
            VALUES
                (%s, %s, %s, %s, %s)
        """
        parametros = (
            nombre_completo,
            numero_comuna,
            carrera_interes,
            fecha_ingreso,
            servidor_origen,
        )

        conexion = None
        cursor = None
        try:
            conexion = self._abrir_conexion()
            cursor = conexion.cursor()
            cursor.execute(sentencia_sql, parametros)
            conexion.commit()
            return cursor.lastrowid
        except ErrorMySQL as error:
            log.error("Error al guardar registro: %s", error)
            if conexion is not None:
                conexion.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None and conexion.is_connected():
                conexion.close()
