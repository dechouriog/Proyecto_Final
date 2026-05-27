# ----------------------------------------------------------------------------
# Imagen para la aplicación web (Flask).
# Usamos python:3.12-slim por su buen balance entre tamaño y compatibilidad.
# ----------------------------------------------------------------------------
FROM python:3.12-slim

# Buenas prácticas de Python en contenedores
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /aplicacion

# Instalamos primero las dependencias (mejor cacheo de capas Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente de la app
COPY src/ ./src/

# Puerto donde escucha Gunicorn
EXPOSE 5000

# Usamos Gunicorn (servidor WSGI de producción) con varios workers
# para soportar peticiones simultáneas como exige la consigna.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "3", \
     "--access-logfile", "-", \
     "--error-logfile",  "-", \
     "src.aplicacion:app"]
