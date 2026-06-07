# factura-co — Comandos de desarrollo y ejecucion

.PHONY: run-app run-tests calcular instalar instalar-app limpiar ayuda

## Ejecutar la aplicacion web Streamlit
run-app:
	streamlit run app/main.py

## Correr toda la suite de tests con salida detallada
run-tests:
	python -m pytest tests/ -v

## Correr tests en modo silencioso (solo errores y resumen)
test:
	python -m pytest tests/ -q

## Mostrar ayuda del CLI de calculo
calcular:
	python scripts/calcular.py --help

## Instalar el paquete en modo desarrollo
instalar:
	pip install -e . --break-system-packages

## Instalar todas las dependencias de la app web
instalar-app:
	pip install -r requirements-app.txt --break-system-packages

## Instalar dependencias de desarrollo
instalar-dev:
	pip install pytest tabulate fpdf2 --break-system-packages

## Calcular ejemplo rapido (honorarios 3M)
ejemplo:
	python scripts/calcular.py --valor 3000000 --tipo honorarios

## Ver todos los tipos de servicio y tarifas
tipos:
	python scripts/calcular.py --listar-tipos

## Limpiar archivos temporales de Python
limpiar:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

## Mostrar este menu de ayuda
ayuda:
	@echo ""
	@echo "  factura-co -- comandos disponibles:"
	@echo ""
	@grep -E '^##' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
