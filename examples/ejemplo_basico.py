"""
ejemplo_basico.py — Demostración del uso de factura-co.

Ejecutar desde la raíz del proyecto:
    python examples/ejemplo_basico.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.calculadora import calcular_neto, generar_resumen
from src.factura_co.documento import generar_documento_txt


print("=" * 65)
print("  FACTURA-CO — Ejemplos de uso")
print("=" * 65)

# ----------------------------------------------------------------
# Caso 1: Diseñador freelance — proyecto de branding
# ----------------------------------------------------------------
print("\n🎨 CASO 1: Diseñadora freelance, proyecto de branding ($4.500.000)")
print("-" * 65)

resultado_1 = calcular_neto(
    valor_factura=4_500_000,
    tipo_servicio="honorarios",
    es_declarante=False,       # No declarante de renta
    incluir_aportes=True,
)
generar_resumen(resultado_1)

# ----------------------------------------------------------------
# Caso 2: Desarrollador — sprint de desarrollo
# ----------------------------------------------------------------
print("\n💻 CASO 2: Desarrollador independiente, sprint ($6.000.000)")
print("-" * 65)

resultado_2 = calcular_neto(6_000_000, "honorarios")
generar_resumen(resultado_2)

# ----------------------------------------------------------------
# Caso 3: Consultor — tarifa de servicios (no honorarios)
# ----------------------------------------------------------------
print("\n📊 CASO 3: Consultor de negocios, servicio de consultoría ($3.500.000)")
print("-" * 65)

resultado_3 = calcular_neto(
    valor_factura=3_500_000,
    tipo_servicio="servicios",
    es_declarante=True,        # Declarante por ingresos altos
)
generar_resumen(resultado_3)

# ----------------------------------------------------------------
# Caso 4: Solo retención, sin aportes (para quien ya tiene salud por otro medio)
# ----------------------------------------------------------------
print("\n🏥 CASO 4: Mismos honorarios, SIN incluir aportes ($3.000.000)")
print("-" * 65)

resultado_4 = calcular_neto(3_000_000, "honorarios", incluir_aportes=False)
generar_resumen(resultado_4)

# ----------------------------------------------------------------
# Generar documento de cobro
# ----------------------------------------------------------------
print("\n📄 CASO 5: Generar documento de cobro")
print("-" * 65)

freelancer = {
    "nombre": "Valentina Ospina",
    "cedula": "1.020.345.678",
    "banco": "Bancolombia",
    "tipo_cuenta": "Ahorros",
    "cuenta": "405-123456-78",
    "ciudad": "Medellín",
    "email": "valentina@diseño.co",
    "telefono": "300 123 4567",
}

cliente = {
    "empresa": "Innovatech Colombia SAS",
    "nit": "901.234.567-8",
    "contacto": "Andrés Ramírez",
    "ciudad": "Bogotá",
}

documento = generar_documento_txt(
    datos_freelancer=freelancer,
    datos_cliente=cliente,
    valor=4_500_000,
    descripcion=(
        "Diseño de identidad visual corporativa: logotipo, manual de marca, "
        "paleta de colores y tipografía institucional."
    ),
    numero="CC-2024-001",
)
print(documento)

print("\n✅ Todos los ejemplos ejecutados correctamente.")
