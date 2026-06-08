#!/usr/bin/env python3
"""
Ejemplo: Generar una factura en PDF lista para enviar al cliente.

Escenario: Una desarrolladora factura un sprint a una empresa y necesita un
documento profesional con el desglose de retención en la fuente.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from factura_co.factura_pdf import generar_factura, guardar_factura, _desglose_factura


def main():
    datos = {
        "nombre_freelancer": "Ana García Restrepo",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": (
            "Desarrollo de API de pagos e integración con pasarela — Sprint 3 "
            "(diseño de endpoints, pruebas y despliegue)"
        ),
        "valor_cop": 5_000_000,
        "retencion_pct": 11,           # honorarios, no declarante (Art. 392 ET)
        "numero_factura": "FV-2026-014",
        "ciudad": "Bogotá D.C.",
        "email": "ana@ejemplo.co",
        "telefono": "300 123 4567",
        "banco": "Bancolombia",
        "cuenta": "123-456789-00",
        "tipo_cuenta": "Ahorros",
        "notas": "Pago a 15 días. Valores en pesos colombianos, no responsable de IVA.",
    }

    # Desglose económico (mismo cálculo que usa el PDF)
    dg = _desglose_factura(datos)
    print("\n" + "=" * 60)
    print(f"  FACTURA {dg['numero']}  ·  {dg['fecha_str']}")
    print("=" * 60)
    print(f"  Subtotal:            ${dg['subtotal']:>14,.0f}")
    print(f"  Retención ({dg['retencion_pct']*100:.0f}%):     -${dg['retencion_valor']:>13,.0f}")
    print("  " + "-" * 40)
    print(f"  TOTAL A PAGAR:       ${dg['total']:>14,.0f}")
    print("=" * 60)

    # Generar y guardar el PDF
    pdf_bytes = generar_factura(datos)
    ruta = guardar_factura(pdf_bytes, "factura_ejemplo.pdf")
    print(f"\n  PDF generado: {ruta}  ({len(pdf_bytes):,} bytes)")


if __name__ == "__main__":
    main()
