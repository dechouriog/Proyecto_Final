# Arquitectura del sistema

## Visión general

El sistema implementa una aplicación web distribuida y segura que permite
a usuarios registrar su interés en estudiar una carrera de pregrado.
La arquitectura sigue los principios de:

- **Separación de responsabilidades**: cada componente tiene una función única.
- **Contenedorización**: todos los servicios corren en Docker para portabilidad.
- **Escalabilidad horizontal**: el balanceador permite añadir más réplicas
  de las apps web sin cambios en el cliente.
- **Seguridad en capas**: SSL en el borde, red interna privada para los servicios.

## Componentes

### 1. Balanceador de carga / Proxy inverso (NGINX)

- **Imagen base**: `nginx:1.27-alpine`
- **Responsabilidades**:
  - Único punto de entrada desde Internet (puertos 80 y 443).
  - Terminación SSL/TLS (HTTPS).
  - Redirección automática HTTP → HTTPS.
  - Distribución de peticiones mediante **round robin** entre las dos
    apps web (política por defecto de NGINX al definir un upstream sin
    especificar otro algoritmo).
  - Cabeceras de proxy (`X-Forwarded-For`, `X-Real-IP`, etc.) para que
    las apps backend sepan la IP real del cliente.
  - Headers de seguridad básicos (X-Frame-Options, X-Content-Type-Options).

### 2. Aplicaciones web (Flask)

Dos instancias idénticas en lógica, pero con idioma fijo distinto:

- **Web Server 1**: idioma fijo en inglés.
- **Web Server 2**: idioma fijo en español.

Ambas usan:
- **Framework**: Flask 3 con Jinja2 para templates.
- **Servidor**: Gunicorn con 3 workers (soporte para peticiones simultáneas).
- **Validación**: tanto en frontend (HTML required) como en backend
  (validación explícita de nombre, comuna 1-10 y carrera).
- **Acceso a datos**: `mysql-connector-python` con consultas parametrizadas
  (prevención de SQL injection).

El identificador del servidor se inyecta por variable de entorno y se
muestra en el pie de página para verificar visualmente el round robin.

### 3. Base de datos (MySQL 8)

- **Imagen base**: `mysql:8.0`
- **Tabla principal**: `registros_interesados` con columnas:
  - `id_registro` (PK, AUTO_INCREMENT)
  - `nombre_completo` (VARCHAR 150)
  - `numero_comuna` (TINYINT, CHECK entre 1 y 10)
  - `carrera_interes` (VARCHAR 50, CHECK lista cerrada)
  - `fecha_ingreso` (DATETIME)
  - `servidor_origen` (VARCHAR 50)
- **Índices** en `numero_comuna`, `carrera_interes` y `fecha_ingreso`
  para acelerar las consultas del servicio de estadísticas.
- **Persistencia**: volumen Docker `datos-mysql`.
- **Aislamiento**: NO expone su puerto al exterior; solo es accesible
  desde la red privada de docker.

### 4. Servicio de estadísticas

- **Framework**: Flask + Gunicorn.
- **Generación de gráficas**: matplotlib en modo `Agg` (sin display).
- **Envío de correo**: `smtplib` estándar de Python + MIMEMultipart.
- **Endpoints**:
  - `GET /` → panel con botón.
  - `POST /enviar-reporte` → ejecuta el pipeline completo.
  - `GET /salud` → healthcheck.
- **Tres gráficas en el reporte**:
  1. Barras: registros por comuna.
  2. Pastel: distribución por carrera.
  3. Barras apiladas: comuna × carrera.

## Flujo de una petición típica

```
1. Usuario abre https://proyecto-eafit.duckdns.org/
2. DNS resuelve a la IP elástica de EC2.
3. La petición llega al puerto 443 de la EC2.
4. NGINX (balanceador) negocia TLS, descifra la petición.
5. NGINX selecciona la siguiente app del upstream (round robin):
     - Primera petición:  app-web-ingles
     - Segunda petición:  app-web-espanol
     - Tercera petición:  app-web-ingles
     - ...
6. NGINX hace forward HTTP plano hacia el container Flask elegido.
7. Flask renderiza el formulario en el idioma correspondiente.
8. Si el método es POST:
     a. Valida datos.
     b. Inserta en MySQL vía consulta parametrizada.
     c. Devuelve mensaje de éxito.
9. NGINX cifra la respuesta y la devuelve al cliente.
```

## Flujo del reporte de estadísticas

```
1. Administrador accede a http://<dominio>:6000/
2. Presiona el botón "Enviar reporte".
3. El JS dispara POST /enviar-reporte.
4. El servicio:
     a. Consulta a MySQL los agregados (totales, por comuna, por carrera, cruce).
     b. Genera tres gráficas PNG con matplotlib (en memoria).
     c. Construye un correo HTML multipart/related con las imágenes inline.
     d. Se conecta vía SMTP (TLS) al servidor configurado.
     e. Autentica y envía el correo al destinatario.
5. Devuelve JSON con el resultado al frontend.
```

## Seguridad

- **HTTPS obligatorio**: HTTP redirige a HTTPS con 301.
- **TLS 1.2+**: protocolos antiguos deshabilitados.
- **Credenciales en variables de entorno**: nunca hardcodeadas en imágenes.
- **Red interna privada**: BD y apps no son accesibles desde fuera.
- **Consultas parametrizadas**: protección contra SQL injection.
- **Validación de entrada**: nombre, comuna y carrera se validan en backend.
- **CHECK constraints en BD**: doble capa de validación.
- **Imágenes Docker minimalistas**: `slim` y `alpine` para reducir superficie.

## Cubrimiento de los entregables operacionales

| # | Requisito | Implementación |
|---|---|---|
| 1 | Acceso por URL, formulario con nombre, comuna (1-10), fecha y carrera | Apps Flask con template `formulario.html`; fecha es automática (DEFAULT CURRENT_TIMESTAMP) |
| 2 | Dominio + registro A en DNS | DuckDNS (instrucciones en guía-despliegue.md) |
| 3 | Balanceador round robin + proxy inverso en Docker | NGINX con upstream y política default round robin |
| 4 | Forward del balanceador a apps en Docker | Cada app es un contenedor con su Dockerfile |
| 5 | Una página en inglés, otra en español | Web Server 1 EN + Web Server 2 ES; idioma fijo por variable de entorno |
| 6 | BD en Docker | MySQL 8 con volumen persistente y script de inicialización |
| 7 | Aplicación de correo con estadísticas por comuna y carrera | servicio-estadisticas con matplotlib + smtplib |
| 8 | HTTPS + simultaneidad | SSL en NGINX + Gunicorn multi-worker |
