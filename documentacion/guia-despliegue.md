# Guía de despliegue - Proyecto EAFIT

Este documento describe paso a paso cómo desplegar el sistema completo,
tanto en una máquina local de pruebas como en una instancia EC2 de AWS.

## Tabla de contenidos

1. Requisitos previos
2. Estructura del proyecto
3. Despliegue local (pruebas)
4. Despliegue en AWS EC2
5. Configuración del dominio y DNS
6. Certificado SSL (Let's Encrypt para producción)
7. Configuración del envío de correo
8. Verificación del round robin
9. Cómo probar el envío del reporte
10. Solución de problemas comunes

---

## 1. Requisitos previos

- Docker 24+ y Docker Compose v2 instalados.
- Git para clonar el repositorio.
- Una cuenta de correo con SMTP habilitado (Gmail con App Password sirve).
- (Producción) Una instancia AWS EC2 con grupo de seguridad abriendo
  los puertos 80, 443 y 6000.
- (Producción) Un dominio gratuito de DuckDNS, No-IP, Freenom o similar.

---

## 2. Estructura del proyecto

```
proyecto-eafit/
├── docker-compose.yml              # Orquesta todos los servicios
├── archivo-variables-entorno.env   # Plantilla de configuración
├── README.md
├── balanceador/                    # NGINX (proxy inverso + load balancer + SSL)
│   ├── Dockerfile
│   ├── generar-certificado.sh
│   ├── config/nginx.conf
│   └── certs/                      # Certificados SSL
├── aplicacion-web-ingles/          # Web Server 1 - Flask, idioma fijo EN
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── aplicacion-web-espanol/         # Web Server 2 - Flask, idioma fijo ES
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── base-de-datos/                  # MySQL
│   └── scripts-inicializacion/01-crear-tabla-registros.sql
└── servicio-estadisticas/          # Servicio que envía reporte por correo
    ├── Dockerfile
    ├── requirements.txt
    └── src/
```

---

## 3. Despliegue local (pruebas)

### Paso 3.1: Clonar el repositorio

```bash
git clone <url-del-repo>
cd proyecto-eafit
```

### Paso 3.2: Configurar variables de entorno

```bash
cp archivo-variables-entorno.env .env
```

Editar `.env` y configurar:

- Contraseñas de MySQL (cualquier valor seguro).
- Credenciales SMTP (ver sección 7).

### Paso 3.3: Generar certificado SSL autofirmado

```bash
cd balanceador
./generar-certificado.sh proyecto-eafit.local
cd ..
```

Esto crea los archivos `certificado-sitio.crt` y `clave-privada.key`
dentro de `balanceador/certs/`.

### Paso 3.4: Levantar los servicios

```bash
docker compose up --build -d
```

La primera vez tardará unos minutos en bajar imágenes y construir.

### Paso 3.5: Verificar que todo está corriendo

```bash
docker compose ps
```

Todos los servicios deben aparecer como `running` o `healthy`.

### Paso 3.6: Acceder a la aplicación

- Aplicación web: `https://localhost/`
  (el navegador advertirá sobre el certificado autofirmado; aceptar
  la excepción para continuar).
- Panel de estadísticas: `http://localhost:6000/`

---

## 4. Despliegue en AWS EC2

### Paso 4.1: Crear la instancia

- AMI: Ubuntu Server 22.04 LTS o Amazon Linux 2023.
- Tipo: t3.small como mínimo (la BD + 2 apps + nginx + estadísticas
  consumen RAM; t2.micro suele quedarse corta).
- Grupo de seguridad - reglas de entrada:
  - SSH (22) desde tu IP.
  - HTTP (80) desde 0.0.0.0/0.
  - HTTPS (443) desde 0.0.0.0/0.
  - Puerto 6000 desde tu IP (solo administrador).
- Asignar IP elástica para que no cambie al reiniciar.

### Paso 4.2: Instalar Docker en la instancia

Conectarse por SSH y ejecutar:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar para que tome efecto el grupo
```

### Paso 4.3: Clonar y desplegar

```bash
git clone <url-del-repo>
cd proyecto-eafit
cp archivo-variables-entorno.env .env
nano .env   # Configurar credenciales reales

cd balanceador
./generar-certificado.sh tu-dominio.duckdns.org
cd ..

docker compose up --build -d
```

---

## 5. Configuración del dominio y DNS

La consigna pide registrar un dominio gratuito y crear un registro A
apuntando al sitio. Recomendamos **DuckDNS** por su simplicidad:

### Paso 5.1: Registrar dominio en DuckDNS

1. Ir a https://www.duckdns.org y autenticarse con Google/GitHub.
2. Crear un subdominio gratuito, por ejemplo `proyecto-eafit.duckdns.org`.
3. En el campo "current ip" poner la **IP elástica** de la EC2.
4. Pulsar "update ip".

Esto equivale a crear un **registro A** apuntando al servidor.

### Paso 5.2: Verificar la resolución DNS

```bash
nslookup proyecto-eafit.duckdns.org
# o
dig proyecto-eafit.duckdns.org +short
```

Debe devolver la IP de la EC2.

---

## 6. Certificado SSL para producción (Let's Encrypt)

El certificado autofirmado funciona pero el navegador da advertencia.
Para uno reconocido, usar Let's Encrypt vía certbot:

### Opción A: Certbot fuera de Docker (más simple)

```bash
sudo apt install -y certbot
# Detener nginx temporalmente para liberar el puerto 80
docker compose stop balanceador-nginx
sudo certbot certonly --standalone -d proyecto-eafit.duckdns.org
# Copiar certificados al proyecto
sudo cp /etc/letsencrypt/live/proyecto-eafit.duckdns.org/fullchain.pem \
        balanceador/certs/certificado-sitio.crt
sudo cp /etc/letsencrypt/live/proyecto-eafit.duckdns.org/privkey.pem \
        balanceador/certs/clave-privada.key
sudo chown $USER:$USER balanceador/certs/*

# Reconstruir nginx con los nuevos certificados
docker compose up --build -d balanceador-nginx
```

Los certificados Let's Encrypt expiran a los 90 días; programar
renovación con `certbot renew` en cron.

---

## 7. Configuración del envío de correo

El servicio de estadísticas requiere credenciales SMTP. Para Gmail:

1. Activar verificación en dos pasos en la cuenta Google.
2. Ir a https://myaccount.google.com/apppasswords
3. Crear una "App password" para "Mail".
4. Copiar la contraseña generada (16 caracteres).
5. En el archivo `.env`:

```
SMTP_SERVIDOR=smtp.gmail.com
SMTP_PUERTO=587
SMTP_USUARIO=tucuenta@gmail.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx
CORREO_REMITENTE=tucuenta@gmail.com
CORREO_DESTINATARIO=ialondonoo@eafit.edu.co
```

6. Reiniciar el servicio:

```bash
docker compose restart servicio-estadisticas
```

---

## 8. Verificación del round robin

El balanceador reparte las peticiones en round robin entre las dos apps.
Para comprobarlo, recargar varias veces la página y observar el pie de
página: alternará entre "Web Server 1 (EN)" y "Web Server 2 (ES)".

También con `curl`:

```bash
for i in {1..6}; do
  curl -sk https://proyecto-eafit.duckdns.org/ | grep -oE "Web Server [12] \([A-Z]+\)"
done
```

Se debe ver alternancia entre los dos servidores.

---

## 9. Cómo probar el envío del reporte

### Paso 9.1: Generar algunos registros

Acceder a `https://<dominio>/` varias veces (recargando) y enviar
registros con diferentes comunas y carreras. Como hay round robin,
unos quedarán registrados desde el server EN y otros desde el ES.

### Paso 9.2: Disparar el envío

Opción A: desde el navegador

- Ir a `http://<dominio>:6000/`
- Presionar el botón "Enviar reporte por correo".

Opción B: por curl

```bash
curl -X POST http://<dominio>:6000/enviar-reporte
```

El correo llegará a la dirección configurada en `CORREO_DESTINATARIO`,
con tres gráficas embebidas:

1. Registros por comuna (barras).
2. Distribución por carrera (pastel).
3. Registros por comuna desglosados por carrera (barras apiladas).

---

## 10. Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `docker compose up` falla al construir nginx | Falta el certificado | Ejecutar `balanceador/generar-certificado.sh` |
| App responde 502 Bad Gateway | Las apps Flask no arrancaron | `docker compose logs app-web-ingles app-web-espanol` |
| BD no acepta conexiones | Aún arrancando | Esperar 20s; el healthcheck retiene a las apps |
| Correo no se envía | Credenciales SMTP malas | Verificar App Password de Gmail; revisar logs del servicio |
| Solo veo un servidor en el footer | Caché del navegador o un Flask caído | Forzar recarga (Ctrl+F5); revisar logs |
| `docker compose ps` muestra "unhealthy" en BD | Password incorrecto en .env | Revisar `MYSQL_PASSWORD_ROOT` |

### Ver logs en vivo

```bash
docker compose logs -f                    # todos los servicios
docker compose logs -f balanceador-nginx  # solo nginx
docker compose logs -f app-web-ingles     # solo app EN
docker compose logs -f servicio-estadisticas
```

### Reiniciar todo desde cero

```bash
docker compose down -v   # CUIDADO: borra el volumen de BD
docker compose up --build -d
```

---

## Apéndice: comprobación rápida del despliegue

Comandos en orden para validar que todo funciona:

```bash
# 1. Servicios arriba
docker compose ps

# 2. Balanceador responde
curl -k https://localhost/salud

# 3. Apps responden directamente (debugging)
docker compose exec balanceador-nginx wget -qO- http://app-web-ingles:5000/salud
docker compose exec balanceador-nginx wget -qO- http://app-web-espanol:5000/salud

# 4. BD acepta conexiones
docker compose exec base-de-datos mysql -uroot -p$MYSQL_PASSWORD_ROOT -e "SHOW DATABASES;"

# 5. Round robin alternando
for i in {1..6}; do curl -sk https://localhost/ | grep -oE "Web Server [12]"; done

# 6. Servicio de estadísticas vivo
curl http://localhost:6000/salud
```
