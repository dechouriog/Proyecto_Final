# Práctica Final - Internet: Arquitectura y Protocolos

## Integrantes

- Diego Eduardo Chourio Garcia
- Leidy Carolina Obando Figueroa

Universidad EAFIT - 2025-2

## Descripción

Sistema de registro de usuarios interesados en estudiar carreras de pregrado.
La aplicación captura nombre, comuna (1-10), fecha y carrera de interés
(Medicina, Ingeniería, Abogacía, Licenciatura).

Toda la arquitectura corre sobre Docker y está pensada para desplegarse en AWS EC2.

## Arquitectura

```
                     Internet (HTTPS)
                           │
                           ▼
              ┌────────────────────────┐
              │  Balanceador NGINX     │  ← Proxy inverso + Round Robin + SSL
              │  (Puerto 443)          │
              └────────┬───────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────┐             ┌───────────────┐
│ Web Server 1  │             │ Web Server 2  │
│   (Inglés)    │             │   (Español)   │
│  Flask :5000  │             │  Flask :5000  │
└───────┬───────┘             └───────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
              ┌────────────────┐
              │  MySQL :3306   │
              │  (Base datos)  │
              └────────┬───────┘
                       │
                       ▼
              ┌────────────────────┐
              │ Servicio Estad.    │  ← Envía reporte por email
              │ Flask :6000        │     con gráficas a admin
              └────────────────────┘
```

## Estructura del repositorio

```
.
├── balanceador/                     # NGINX como proxy inverso + load balancer
│   ├── config/                      # Configuración nginx.conf
│   ├── certs/                       # Certificados SSL autofirmados
│   └── Dockerfile
├── aplicacion-web-ingles/           # Web Server 1 - idioma fijo en inglés
│   ├── src/                         # Código Flask + templates
│   └── Dockerfile
├── aplicacion-web-espanol/          # Web Server 2 - idioma fijo en español
│   ├── src/
│   └── Dockerfile
├── base-de-datos/                   # MySQL con script de inicialización
│   └── scripts-inicializacion/
├── servicio-estadisticas/           # App que genera reporte con gráficas y envía por correo
│   ├── src/
│   └── Dockerfile
├── docker-compose.yml               # Orquestación de todos los servicios
├── archivo-variables-entorno.env    # Plantilla de variables sensibles
└── documentacion/
    └── guia-despliegue.md
```

## Cómo levantar el proyecto

1. Generar certificado SSL autofirmado (ver `balanceador/generar-certificado.sh`).
2. Copiar `archivo-variables-entorno.env` a `.env` y configurar credenciales.
3. Construir y levantar:

```bash
docker compose up --build -d
```

4. Acceder en navegador:
   - `https://<tu-dominio-o-IP>/` (round robin entre las dos apps)
   - `http://<tu-dominio-o-IP>:6000/enviar-reporte` para disparar el envío de estadísticas.

Más detalles en `documentacion/guia-despliegue.md`.

## Integrantes

(Completar con los nombres del equipo)

## Entregables operacionales cubiertos

- [x] Sitio accesible por URL con formulario (nombre, comuna 1-10, fecha, carrera).
- [x] DNS con registro A apuntando al balanceador (instrucciones en guía).
- [x] Balanceador NGINX con round robin y proxy inverso.
- [x] Dos web servers en Docker (uno en inglés, otro en español).
- [x] Base de datos MySQL en Docker para persistir registros.
- [x] Servicio de estadísticas con gráficas que envía email al administrador.
- [x] Acceso por HTTPS con certificado SSL.
- [x] Soporta peticiones simultáneas (Flask + Gunicorn).
