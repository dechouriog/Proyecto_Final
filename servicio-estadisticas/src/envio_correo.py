"""
Módulo de envío de correo del reporte de estadísticas.

Construye un correo multipart/related con HTML + imágenes inline (las
gráficas) y lo envía vía SMTP. La configuración se toma de variables
de entorno.
"""

import logging
import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)


def enviar_correo_con_reporte(estadisticas: dict, graficas_png: dict, fecha_generacion) -> None:
    """
    Envía un correo HTML con las gráficas embebidas inline.

    Lanza excepción si algo falla (la maneja el caller).
    """
    # --- Configuración SMTP desde variables de entorno --------------------
    servidor_smtp     = os.getenv("SMTP_SERVIDOR", "smtp.gmail.com")
    puerto_smtp       = int(os.getenv("SMTP_PUERTO", "587"))
    usuario_smtp      = os.getenv("SMTP_USUARIO", "")
    password_smtp     = os.getenv("SMTP_PASSWORD", "")
    correo_remitente  = os.getenv("CORREO_REMITENTE", usuario_smtp)
    correo_destinatario = os.getenv("CORREO_DESTINATARIO", "ialondonoo@eafit.edu.co")

    if not usuario_smtp or not password_smtp:
        raise RuntimeError(
            "Faltan credenciales SMTP. Configura SMTP_USUARIO y SMTP_PASSWORD."
        )

    # --- Construcción del mensaje ----------------------------------------
    mensaje = MIMEMultipart("related")
    mensaje["Subject"] = (
        f"Reporte de Estadísticas - Registros EAFIT "
        f"({fecha_generacion.strftime('%Y-%m-%d %H:%M')})"
    )
    mensaje["From"] = correo_remitente
    mensaje["To"]   = correo_destinatario

    # Parte alternativa: HTML (y un fallback en texto plano)
    parte_alternativa = MIMEMultipart("alternative")
    mensaje.attach(parte_alternativa)

    cuerpo_texto_plano = _construir_cuerpo_texto_plano(estadisticas, fecha_generacion)
    cuerpo_html        = _construir_cuerpo_html(estadisticas, fecha_generacion)

    parte_alternativa.attach(MIMEText(cuerpo_texto_plano, "plain", "utf-8"))
    parte_alternativa.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    # Adjuntamos cada gráfica como inline (Content-ID que referencian los <img>)
    for nombre, bytes_png in graficas_png.items():
        imagen = MIMEImage(bytes_png, _subtype="png")
        imagen.add_header("Content-ID", f"<{nombre}>")
        imagen.add_header("Content-Disposition", "inline", filename=f"{nombre}.png")
        mensaje.attach(imagen)

    # --- Envío SMTP -------------------------------------------------------
    log.info("Conectando a SMTP %s:%s", servidor_smtp, puerto_smtp)
    with smtplib.SMTP(servidor_smtp, puerto_smtp, timeout=30) as cliente:
        cliente.ehlo()
        cliente.starttls()
        cliente.ehlo()
        cliente.login(usuario_smtp, password_smtp)
        cliente.send_message(mensaje)

    log.info("Correo enviado a %s", correo_destinatario)


# ===========================================================================
# Construcción del contenido del correo
# ===========================================================================

def _construir_cuerpo_texto_plano(estadisticas: dict, fecha) -> str:
    """Versión texto plano (fallback si el cliente no soporta HTML)."""
    lineas = [
        "REPORTE DE ESTADÍSTICAS - REGISTROS EAFIT",
        f"Generado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total de registros acumulados: {estadisticas['total_registros']}",
        "",
        "Registros por comuna:",
    ]
    for comuna in sorted(estadisticas["conteo_por_comuna"]):
        cantidad = estadisticas["conteo_por_comuna"][comuna]
        lineas.append(f"  - Comuna {comuna}: {cantidad}")

    lineas.append("")
    lineas.append("Registros por carrera:")
    for carrera in sorted(estadisticas["conteo_por_carrera"]):
        cantidad = estadisticas["conteo_por_carrera"][carrera]
        lineas.append(f"  - {carrera}: {cantidad}")

    lineas.append("")
    lineas.append("Detalle por comuna y carrera:")
    for comuna in sorted(estadisticas["conteo_comuna_carrera"]):
        carreras_comuna = estadisticas["conteo_comuna_carrera"][comuna]
        for carrera in sorted(carreras_comuna):
            cantidad = carreras_comuna[carrera]
            lineas.append(f"  - Comuna {comuna} / {carrera}: {cantidad}")

    return "\n".join(lineas)


def _construir_cuerpo_html(estadisticas: dict, fecha) -> str:
    """
    Versión HTML del correo. Las gráficas se referencian con cid:nombre
    para que aparezcan inline en clientes de correo modernos.
    """
    filas_tabla_comuna = "".join(
        f"<tr><td>Comuna {comuna}</td><td style='text-align:right'><strong>{cantidad}</strong></td></tr>"
        for comuna, cantidad in sorted(estadisticas["conteo_por_comuna"].items())
    )
    filas_tabla_carrera = "".join(
        f"<tr><td>{carrera}</td><td style='text-align:right'><strong>{cantidad}</strong></td></tr>"
        for carrera, cantidad in sorted(estadisticas["conteo_por_carrera"].items())
    )

    return f"""\
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; color: #1d2533; max-width: 720px; margin: 0 auto; padding: 20px;">

  <div style="background: #003366; color: white; padding: 24px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 22px;">Reporte de Estadísticas</h1>
    <p style="margin: 6px 0 0 0; opacity: 0.85;">
      Registros acumulados de interesados - Universidad EAFIT<br>
      Generado: {fecha.strftime('%Y-%m-%d %H:%M:%S')}
    </p>
  </div>

  <div style="background: #f4f6f9; padding: 20px; border-radius: 0 0 8px 8px;">

    <div style="background: white; padding: 18px; border-radius: 6px; margin-bottom: 18px;
                border-left: 4px solid #d4a017;">
      <strong style="font-size: 16px;">Total de registros:</strong>
      <span style="font-size: 22px; color: #003366; font-weight: bold; margin-left: 10px;">
        {estadisticas['total_registros']}
      </span>
    </div>

    <h2 style="color: #003366;">Registros por comuna</h2>
    <img src="cid:grafica_por_comuna"
         alt="Gráfica por comuna"
         style="width: 100%; max-width: 700px; border-radius: 6px; background: white;" />

    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: white;">
      <thead>
        <tr style="background: #003366; color: white;">
          <th style="padding: 8px; text-align: left;">Comuna</th>
          <th style="padding: 8px; text-align: right;">Registros</th>
        </tr>
      </thead>
      <tbody>{filas_tabla_comuna}</tbody>
    </table>

    <h2 style="color: #003366; margin-top: 30px;">Distribución por carrera</h2>
    <img src="cid:grafica_por_carrera"
         alt="Gráfica por carrera"
         style="width: 100%; max-width: 500px; border-radius: 6px; background: white; display: block; margin: 0 auto;" />

    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: white;">
      <thead>
        <tr style="background: #003366; color: white;">
          <th style="padding: 8px; text-align: left;">Carrera</th>
          <th style="padding: 8px; text-align: right;">Registros</th>
        </tr>
      </thead>
      <tbody>{filas_tabla_carrera}</tbody>
    </table>

    <h2 style="color: #003366; margin-top: 30px;">Detalle: comuna × carrera</h2>
    <img src="cid:grafica_comuna_carrera"
         alt="Gráfica por comuna y carrera"
         style="width: 100%; max-width: 700px; border-radius: 6px; background: white;" />

    <p style="color: #6c7280; font-size: 12px; margin-top: 30px; text-align: center;">
      Reporte generado automáticamente por el servicio de estadísticas.
    </p>
  </div>
</body>
</html>
"""
