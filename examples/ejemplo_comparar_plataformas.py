#!/usr/bin/env python3
"""
Ejemplo: Comparar plataformas de pago para un freelancer colombiano.

Escenario: Diseñador UX recibe $1.500 USD de cliente en Estados Unidos.
¿Por qué plataforma llegan más pesos a su cuenta?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from factura_co.comparador import tabla_comparacion, comparar_plataformas
from factura_co.plataformas import calcular_neto_plataforma
from factura_co.trm_live import get_trm_info

def main():
    print("\n" + "=" * 70)
    print("  CASO REAL: Diseñador UX recibe $1.500 USD de cliente en EE.UU.")
    print("=" * 70)

    # TRM actual
    info_trm = get_trm_info()
    trm = info_trm["trm"]
    print(f"\n  TRM consultada: ${trm:,.2f} COP/USD  (fuente: {info_trm['fuente']})")

    valor_usd = 1500

    # Tabla completa
    print(tabla_comparacion(valor_usd, trm, tipo_upwork="medio"))

    # Análisis de caso Upwork específico
    print("\n" + "=" * 70)
    print("  ANÁLISIS UPWORK: Impacto del historial con el cliente")
    print("=" * 70)
    for tramo in ["nuevo", "medio", "senior"]:
        r = calcular_neto_plataforma(valor_usd, "upwork", trm, tipo_upwork=tramo)
        print(
            f"  {tramo.upper():<8}  Comisión: {r['comision_pct']*100:.0f}%  "
            f"  Recibe: ${r['valor_cop']:>12,.0f} COP"
        )

    # Consejo final
    print()
    todos = comparar_plataformas(valor_usd, trm)
    mejor = todos[0]
    peor = todos[-1]
    ahorro = mejor["valor_cop"] - peor["valor_cop"]
    print(f"  Diferencia entre mejor ({mejor['plataforma']}) y peor ({peor['plataforma']}): "
          f"${ahorro:,.0f} COP")
    print(f"  En 12 meses de facturación: ${ahorro * 12:,.0f} COP de diferencia")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
