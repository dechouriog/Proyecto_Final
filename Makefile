# ----------------------------------------------------------------------------
# Comandos cómodos para operar el proyecto.
# Uso: make <objetivo>
# ----------------------------------------------------------------------------

.PHONY: help certificado configurar levantar bajar reiniciar logs estado limpiar prueba-round-robin

# Objetivo por defecto: mostrar ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make certificado          - Genera certificado SSL autofirmado"
	@echo "  make configurar           - Copia el template .env si no existe"
	@echo "  make levantar             - Construye y arranca todos los servicios"
	@echo "  make bajar                - Detiene y elimina los contenedores"
	@echo "  make reiniciar            - Reinicia los servicios sin reconstruir"
	@echo "  make logs                 - Muestra los logs en vivo"
	@echo "  make estado               - Estado de los contenedores"
	@echo "  make prueba-round-robin   - Hace 10 peticiones y muestra qué server respondió"
	@echo "  make limpiar              - Borra todo incluyendo el volumen de BD"

certificado:
	cd balanceador && ./generar-certificado.sh proyecto-eafit.local

configurar:
	@if [ ! -f .env ]; then \
		cp archivo-variables-entorno.env .env; \
		echo ".env creado. EDITAR antes de levantar los servicios."; \
	else \
		echo ".env ya existe, no se sobreescribe."; \
	fi

levantar:
	docker compose up --build -d
	@echo ""
	@echo "Servicios levantados. Acceso:"
	@echo "  - App:           https://localhost/"
	@echo "  - Estadísticas:  http://localhost:6000/"

bajar:
	docker compose down

reiniciar:
	docker compose restart

logs:
	docker compose logs -f --tail=80

estado:
	docker compose ps

prueba-round-robin:
	@echo "Haciendo 10 peticiones para verificar round robin..."
	@for i in $$(seq 1 10); do \
		curl -sk https://localhost/ | grep -oE "Web Server [12] \([A-Z]+\)" || echo "(sin respuesta)"; \
	done

limpiar:
	docker compose down -v
	@echo "Contenedores y volumen de BD eliminados."
