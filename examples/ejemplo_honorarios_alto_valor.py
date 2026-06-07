"""
ejemplo_honorarios_alto_valor.py
=================================
Freelancer con honorarios de alto valor (> 4 SMMLV mensuales).

CONTEXTO TRIBUTARIO:
    Cuando un profesional independiente factura más de 4 SMMLV al mes
    (~$5.200.000 en 2024), aplican las siguientes reglas:

    1. RETENCIÓN EN LA FUENTE (Art. 392 E.T.)
       - Tipo: honorarios (servicios técnicos, profesionales, científicos)
       - Tarifa no declarante: 11%  |  Tarifa declarante: 10%
       - Base mínima: ninguna (aplica desde el primer peso)
       - El pagador (empresa cliente) retiene y consigna a la DIAN

    2. APORTES A SEGURIDAD SOCIAL (Ley 1607 de 2012, Art. 26)
       - IBC = 40% del ingreso bruto
       - Salud: 12.5% del IBC  |  Pensión: 16% del IBC
       - Con ingresos altos, el IBC supera 1 SMMLV → se usa el IBC real

    3. IMPUESTO DE RENTA (referencia)
       - Si los ingresos anuales superan ~1.400 UVT ($65.9M en 2024),
         el freelancer está obligado a declarar renta.
       - En ese caso, aplica tarifa declarante (10%) en lugar del 11%.

CASO:
    Desarrollador senior factura $12.000.000 en el mes a empresa pagadora.
    Tiene plan de salud por declaración de renta el año anterior.
    Factura como "honorarios" (Art. 392 ET).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.calculadora import calcular_neto, generar_resumen
from src.factura_co.retenciones import calcular_retencion, UVT_2024
from src.factura_co.aportes import calcular_aportes
from src.factura_co.documento_pdf import generar_pdf, guardar_pdf

# ── Parámetros del caso ───────────────────────────────────────────────────────
VALOR_FACTURA = 12_000_000   # $12.000.000 — alto valor (> 4 SMMLV)
ES_DECLARANTE = True         # Ingresos anuales ~$144M → obligado a declarar

print("=" * 65)
print("  EJEMPLO: HONORARIOS ALTO VALOR — DESARROLLADOR SENIOR")
print("=" * 65)
print(f"  Valor factura: ${VALOR_FACTURA:,.0f}")
print(f"  Condición fiscal: {'declarante de renta' if ES_DECLARANTE else 'no declarante'}")
print()

# ── Comparativa declarante vs. no declarante ──────────────────────────────────
print("  COMPARATIVA DE TARIFAS DE RETENCIÓN:")
print()
for declarante, etiqueta in [(False, "No declarante (11%)"), (True, "Declarante (10%)")]:
    r = calcular_retencion(VALOR_FACTURA, "honorarios", es_declarante=declarante)
    print(f"  {etiqueta}:")
    print(f"    Retención: ${r['valor_retencion']:,.0f}")
    print(f"    Diferencia vs. no declarante: ${r['valor_retencion'] - calcular_retencion(VALOR_FACTURA, 'honorarios', False)['valor_retencion']:,.0f}")
    print()

# ── Cálculo principal ─────────────────────────────────────────────────────────
resultado = calcular_neto(
    valor_factura=VALOR_FACTURA,
    tipo_servicio="honorarios",
    es_declarante=ES_DECLARANTE,
    incluir_aportes=True,
)

print()
generar_resumen(resultado)

# ── Desglose detallado de aportes ─────────────────────────────────────────────
aportes = resultado["aportes"]
print()
print("  DETALLE DE APORTES (alto valor — IBC real, no mínimo):")
print(f"    IBC calculado (40% × $12.000.000): ${aportes['ibc_info']['ibc_calculado']:,.0f}")
print(f"    Ajuste aplicado: {aportes['ibc_info']['ajuste_aplicado']}")
print(f"    IBC que se usa:                    ${aportes['ibc']:,.0f}")
print(f"    Salud (12.5% × IBC):               ${aportes['aporte_salud']:,.0f}")
print(f"    Pensión (16% × IBC):               ${aportes['aporte_pension']:,.0f}")
print()

# ── Generar PDF del documento ─────────────────────────────────────────────────
freelancer = {
    "nombre": "Carlos Rincon Vargas",
    "cedula": "79.123.456",
    "ciudad": "Bogota D.C.",
    "email": "carlos.rincon@ejemplo.com",
    "banco": "Davivienda",
    "cuenta": "0055-1234-5678",
    "tipo_cuenta": "Corriente",
}
cliente = {
    "empresa": "Soluciones Digitales S.A.S.",
    "nit": "901.234.567-8",
    "contacto": "Maria Gomez",
    "ciudad": "Bogota",
}

pdf_bytes = generar_pdf(
    datos_freelancer=freelancer,
    datos_cliente=cliente,
    valor=VALOR_FACTURA,
    descripcion=(
        "Desarrollo de microservicio de autenticacion y autorizacion "
        "(OAuth2 + JWT). Incluye documentacion tecnica y pruebas unitarias. "
        "Periodo: octubre 2024."
    ),
    incluir_retencion=True,
    tarifa_retencion=0.10,   # declarante
    incluir_aportes=True,
    aporte_salud=aportes["aporte_salud"],
    aporte_pension=aportes["aporte_pension"],
)

ruta_pdf = "/tmp/cuenta_cobro_alto_valor.pdf"
guardar_pdf(pdf_bytes, ruta_pdf)
print(f"  PDF generado: {ruta_pdf} ({len(pdf_bytes):,} bytes)")
print()

# ── Punto clave: umbral de declarante ────────────────────────────────────────
uvt = UVT_2024
umbral_declarante_anual = 1_400 * uvt
print("  REFERENCIA — UMBRAL PARA DECLARAR RENTA (2024):")
print(f"    1.400 UVT × ${uvt:,} = ${umbral_declarante_anual:,.0f} al año")
print(f"    Ingreso mensual que activa declaración: ${umbral_declarante_anual / 12:,.0f}")
print(f"    Este caso ({VALOR_FACTURA / (umbral_declarante_anual / 12):.1f}x el umbral mensual) → declarante")
