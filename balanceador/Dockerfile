# ----------------------------------------------------------------------------
# Imagen del balanceador de carga / proxy inverso.
# Usa NGINX oficial y le inyecta nuestra configuración personalizada y
# los certificados SSL.
# ----------------------------------------------------------------------------
FROM nginx:1.27-alpine

# Quitamos la configuración por defecto que trae NGINX
RUN rm /etc/nginx/conf.d/default.conf

# Copiamos nuestra configuración: round robin entre las dos apps, SSL, proxy inverso
COPY config/nginx.conf /etc/nginx/conf.d/default.conf

# Copiamos los certificados SSL (generados con generar-certificado.sh)
COPY certs/certificado-sitio.crt /etc/nginx/certs/certificado-sitio.crt
COPY certs/clave-privada.key /etc/nginx/certs/clave-privada.key

# NGINX expone HTTP y HTTPS
EXPOSE 80 443

# El comando por defecto de la imagen base ya arranca nginx en foreground
