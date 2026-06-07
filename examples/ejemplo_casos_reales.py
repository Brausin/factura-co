#!/usr/bin/env python3
"""
ejemplo_casos_reales.py — Casos de uso reales documentados para freelancers colombianos.

Reproduce exactamente los escenarios del apartado "Casos de uso" de la app web.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from factura_co.calculadora import calcular_neto, generar_resumen
from factura_co.retenciones import calcular_ica, obtener_uvt

UVT = obtener_uvt()
print(f"UVT vigente: ${UVT:,}\n")


# ─── Caso 1: Desarrollador web ───────────────────────────────────────────────
print("=" * 60)
print("CASO 1: Desarrollador web — Honorarios $5.000.000")
print("=" * 60)
r1 = calcular_neto(5_000_000, "honorarios", es_declarante=False)
generar_resumen(r1)
print()

# ─── Caso 2: Diseñadora — debajo del umbral ──────────────────────────────────
print("=" * 60)
print("CASO 2: Disenadora — Servicios $1.800.000")
print(f"  Umbral minimo servicios: 4 UVT = ${4 * UVT:,}")
print("=" * 60)
r2 = calcular_neto(1_800_000, "servicios", es_declarante=False)
base_min = r2["retencion"].get("base_minima_uvt", 0) * UVT
if base_min > 0 and 1_800_000 < base_min:
    print(f"  AVISO: $1.800.000 < umbral ${base_min:,.0f} — no aplica retencion en la fuente")
generar_resumen(r2)
print()

# ─── Caso 3: Abogado declarante ──────────────────────────────────────────────
print("=" * 60)
print("CASO 3: Abogado — Honorarios $15.000.000 (declarante de renta)")
print("=" * 60)
r3 = calcular_neto(15_000_000, "honorarios", es_declarante=True)
generar_resumen(r3)
print()

# ─── Caso 4: Consultor con ReteICA Bogotá ────────────────────────────────────
print("=" * 60)
print("CASO 4: Consultora — $8.000.000 honorarios + ReteICA Bogota")
print("=" * 60)
r4 = calcular_neto(8_000_000, "honorarios", es_declarante=False)
ica = calcular_ica(8_000_000, "bogota", "servicios_profesionales")
neto_con_ica = r4["neto"] - ica["valor_ica"]
generar_resumen(r4)
print(f"  ReteICA Bogota ({ica['tarifa_por_mil']}‰): -${ica['valor_ica']:,}")
print(f"  Neto final con ICA: ${neto_con_ica:,}  ({neto_con_ica/8_000_000*100:.1f}%)")
print()

# ─── Calculadora inversa: cuánto facturar para recibir $4.000.000 ────────────
print("=" * 60)
print("CALCULO INVERSO: Cuanto facturar para recibir $4.000.000 netos?")
print("  (honorarios, no declarante, con aportes SS)")
print("=" * 60)

neto_objetivo = 4_000_000
bruto = float(neto_objetivo)
for _ in range(60):
    r_temp = calcular_neto(bruto, "honorarios", False, True)
    diff = neto_objetivo - r_temp["neto"]
    if abs(diff) < 500:
        break
    bruto += diff * 1.2

bruto_final = round(bruto / 1000) * 1000
r_final = calcular_neto(bruto_final, "honorarios", False, True)
print(f"  Para recibir ~${neto_objetivo:,} netos:")
print(f"  Debes facturar: ${bruto_final:,}")
print(f"  Neto obtenido:  ${r_final['neto']:,}")
print()
