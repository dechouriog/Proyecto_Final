#!/usr/bin/env bash
# ----------------------------------------------------------------------------
# Genera un certificado SSL autofirmado para desarrollo / pruebas.
#
# Para producción real lo ideal es usar Let's Encrypt con certbot una vez
# tengas un dominio apuntando al servidor (ver documentacion/guia-despliegue.md).
#
# Uso:
#   ./generar-certificado.sh [nombre-de-dominio]
#
# Ejemplo:
#   ./generar-certificado.sh mi-app.duckdns.org
# ----------------------------------------------------------------------------

set -euo pipefail

# Si no se pasa dominio, usamos uno genérico
NOMBRE_DOMINIO="${1:-eafit-proyecto.local}"

# Carpeta donde se guardarán los certificados (la misma que monta el Dockerfile)
DIRECTORIO_CERTIFICADOS="$(dirname "$0")/certs"
mkdir -p "$DIRECTORIO_CERTIFICADOS"

echo "Generando certificado autofirmado para: $NOMBRE_DOMINIO"
echo "Validez: 365 días"

openssl req -x509 \
    -nodes \
    -newkey rsa:2048 \
    -keyout "$DIRECTORIO_CERTIFICADOS/clave-privada.key" \
    -out    "$DIRECTORIO_CERTIFICADOS/certificado-sitio.crt" \
    -days 365 \
    -subj "/C=CO/ST=Antioquia/L=Medellin/O=Universidad EAFIT/OU=Practica Final/CN=${NOMBRE_DOMINIO}" \
    -addext "subjectAltName=DNS:${NOMBRE_DOMINIO},DNS:localhost,IP:127.0.0.1"

echo ""
echo "Listo. Archivos generados:"
echo "  - $DIRECTORIO_CERTIFICADOS/certificado-sitio.crt"
echo "  - $DIRECTORIO_CERTIFICADOS/clave-privada.key"
echo ""
echo "Los navegadores mostrarán advertencia de certificado no confiable porque"
echo "es autofirmado. Para producción usa Let's Encrypt (instrucciones en la guía)."
