# ----------------------------------------------------------------------------
# Imagen para el servicio de estadísticas.
# Genera gráficas con matplotlib y envía un correo al administrador con el
# reporte acumulado de registros por comuna y carrera.
# ----------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /servicio

# Instalación de dependencias del sistema necesarias para matplotlib
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libfreetype6 \
        libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 6000

CMD ["gunicorn", \
     "--bind", "0.0.0.0:6000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile",  "-", \
     "src.servicio_reportes:app"]
