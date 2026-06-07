"""
ejemplo_servicios_empresa.py
==============================
Empresa que contrata servicios de mantenimiento a un proveedor externo.

CONTEXTO TRIBUTARIO:
    Los "servicios" (Art. 392 E.T.) se diferencian de los "honorarios" en que
    los segundos corresponden a actividades de naturaleza intelectual o técnica
    especializada (profesiones liberales), mientras que los servicios en general
    incluyen actividades manuales, de mantenimiento, limpieza, vigilancia, etc.

    REGLAS CLAVE PARA SERVICIOS (Art. 392 + Decreto 2418/2013):
    1. Tarifa declarante: 4%   |   No declarante: 6%
    2. BASE MÍNIMA: la retención solo aplica si el valor del pago
       es igual o mayor a 4 UVT.
       - 4 UVT × $47.065 (2024) = $188.260
       - 4 UVT × $49.799 (2025) = $199.196
    3. Por debajo de la base mínima → NO hay retención.

    RETEICA (Impuesto de Industria y Comercio):
    Si la empresa pagadora tiene sede en Bogotá y el servicio se presta en
    Bogotá, también puede retener ICA:
    - Actividades de servicios en general (Bogotá): 4.14 por mil (‰)
    - Se suma a la retención en la fuente como otro descuento.

CASO:
    Empresa de logística contrata servicio de mantenimiento de aires
    acondicionados a un técnico independiente. Valor: $2.500.000.
    Se comparan tres escenarios de valor para ilustrar la base mínima.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.calculadora import calcular_neto
from src.factura_co.retenciones import calcular_retencion, calcular_ica, obtener_uvt

uvt = obtener_uvt()
BASE_MINIMA_SERVICIOS = 4 * uvt

print("=" * 65)
print("  EJEMPLO: SERVICIOS DE MANTENIMIENTO — EMPRESA CONTRATANTE")
print("=" * 65)
print(f"  UVT vigente: ${uvt:,}")
print(f"  Base mínima para retención en servicios: ${BASE_MINIMA_SERVICIOS:,.0f} (4 UVT)")
print()

# ── Escenario 1: valor POR DEBAJO de la base mínima ──────────────────────────
valor_bajo = 150_000
r_bajo = calcular_retencion(valor_bajo, "servicios")
print("  ESCENARIO 1: Pago por debajo de la base mínima")
print(f"    Valor: ${valor_bajo:,.0f} (< ${BASE_MINIMA_SERVICIOS:,.0f})")
print(f"    ¿Aplica retención?: {'SÍ' if r_bajo['aplica'] else 'NO'}")
print(f"    Retención: ${r_bajo['valor_retencion']:,.0f}")
print(f"    Valor a recibir: ${r_bajo['valor_neto']:,.0f}  (= valor bruto, sin retención)")
print()

# ── Escenario 2: valor EXACTAMENTE en la base mínima ─────────────────────────
r_base = calcular_retencion(BASE_MINIMA_SERVICIOS, "servicios")
print("  ESCENARIO 2: Pago en el umbral de la base mínima")
print(f"    Valor: ${BASE_MINIMA_SERVICIOS:,.0f} (= 4 UVT exactos)")
print(f"    ¿Aplica retención?: {'SÍ' if r_base['aplica'] else 'NO'}")
print(f"    Retención (6%): ${r_base['valor_retencion']:,.0f}")
print(f"    Valor a recibir: ${r_base['valor_neto']:,.0f}")
print()

# ── Escenario 3: valor real del contrato ($2.500.000) ─────────────────────────
VALOR_CONTRATO = 2_500_000
resultado = calcular_neto(
    valor_factura=VALOR_CONTRATO,
    tipo_servicio="servicios",
    es_declarante=False,
    incluir_aportes=True,
)

print("  ESCENARIO 3: Contrato de mantenimiento por $2.500.000")
print(f"    Retención en la fuente (6%): ${resultado['valor_retenido']:,.0f}")

# ReteICA en Bogotá para servicios generales
ica = calcular_ica(VALOR_CONTRATO, "bogota", "servicios_generales")
print(f"    ReteICA Bogotá (4.14‰):     ${ica['valor_ica']:,.0f}")
print(f"    Referencia: {ica['descripcion_fuente']}")

total_descuentos = resultado["valor_retenido"] + ica["valor_ica"]
neto_con_ica = VALOR_CONTRATO - total_descuentos
aportes = resultado["aportes"]

print()
print(f"    Valor bruto:                 ${VALOR_CONTRATO:>12,.0f}")
print(f"    - Retefuente (6%):          -${resultado['valor_retenido']:>12,.0f}")
print(f"    - ReteICA (4.14‰):          -${ica['valor_ica']:>12,.0f}")
print(f"    Valor que transfiere cliente: ${neto_con_ica:>11,.0f}")
print()
print(f"    Aportes a pagar (SGSS):      ${aportes['total_aportes']:>12,.0f}")
print(f"      Salud:  ${aportes['aporte_salud']:,.0f}  |  Pensión: ${aportes['aporte_pension']:,.0f}")
print()
neto_final = neto_con_ica - aportes["total_aportes"]
pct = neto_final / VALOR_CONTRATO * 100
print(f"    NETO FINAL:                  ${neto_final:>12,.0f}  ({pct:.1f}% del bruto)")
print()

# ── Nota explicativa ──────────────────────────────────────────────────────────
print("  NOTA: ¿Honorarios o Servicios?")
print("    - Honorarios: actividad intelectual / profesión liberal")
print("      (diseño, programación, asesoría jurídica, consultoría...)")
print("    - Servicios: actividad no intelectual o mixta")
print("      (mantenimiento, instalación, mensajería, vigilancia...)")
print("    La distinción la determina el Código de Actividad Económica (CIIU)")
print("    y la naturaleza del contrato. En caso de duda, aplica honorarios.")
