#!/usr/bin/env python3
"""
calcular.py — CLI para calcular retenciones y aportes desde la terminal.

Uso:
    python calcular.py --valor 3000000 --tipo honorarios
    python calcular.py --valor 5000000 --tipo servicios --declarante
    python calcular.py --valor 2000000 --tipo honorarios --sin-aportes
    python calcular.py --listar-tipos
"""

import argparse
import sys
import os

# Agregar la raíz del proyecto al path para importar factura_co
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.factura_co.calculadora import calcular_neto, generar_resumen
    from src.factura_co.retenciones import listar_tipos_servicio
except ImportError:
    # Intentar importación directa si está instalado como paquete
    from factura_co.calculadora import calcular_neto, generar_resumen
    from factura_co.retenciones import listar_tipos_servicio


def formatear_tabla_tipos():
    """Imprime una tabla con los tipos de servicio disponibles."""
    tipos = listar_tipos_servicio()
    print("\n" + "=" * 75)
    print("  TIPOS DE SERVICIO DISPONIBLES")
    print("=" * 75)
    header = f"  {'Tipo':<15} {'Descripción':<35} {'Declarante':>10} {'No decl.':>10}"
    print(header)
    print("-" * 75)
    for tipo, info in tipos.items():
        desc = info["descripcion"][:33]
        print(
            f"  {tipo:<15} {desc:<35} {info['tarifa_declarante']:>10} "
            f"{info['tarifa_no_declarante']:>10}"
        )
    print("=" * 75)
    print("  Nota: 'Declarante' aplica si tus ingresos anuales superan ~$65M")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="factura-co: Calculadora de retenciones y aportes para freelancers colombianos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python calcular.py --valor 3000000 --tipo honorarios
  python calcular.py --valor 5000000 --tipo servicios --declarante
  python calcular.py --valor 1500000 --tipo honorarios --sin-aportes
  python calcular.py --listar-tipos
        """,
    )

    parser.add_argument(
        "--valor",
        type=float,
        metavar="PESOS",
        help="Valor bruto de la factura en pesos colombianos (ej: 3000000)",
    )
    parser.add_argument(
        "--tipo",
        type=str,
        default="honorarios",
        metavar="TIPO",
        choices=["honorarios", "servicios", "arrendamiento", "compras", "transporte"],
        help="Tipo de servicio (default: honorarios)",
    )
    parser.add_argument(
        "--declarante",
        action="store_true",
        default=False,
        help="Usar tarifas para declarantes de renta (default: no declarante)",
    )
    parser.add_argument(
        "--sin-aportes",
        action="store_true",
        default=False,
        help="No incluir cálculo de aportes a salud y pensión",
    )
    parser.add_argument(
        "--listar-tipos",
        action="store_true",
        default=False,
        help="Mostrar tabla de tipos de servicio y tarifas",
    )

    args = parser.parse_args()

    if args.listar_tipos:
        formatear_tabla_tipos()
        return

    if args.valor is None:
        parser.print_help()
        print("\n❌ Error: --valor es requerido\n")
        sys.exit(1)

    if args.valor <= 0:
        print(f"\n❌ Error: El valor debe ser positivo (recibido: {args.valor})\n")
        sys.exit(1)

    print(f"\nCalculando para: ${args.valor:,.0f} — {args.tipo}")
    if args.declarante:
        print("  (usando tarifas para declarantes de renta)")

    resultado = calcular_neto(
        valor_factura=args.valor,
        tipo_servicio=args.tipo,
        es_declarante=args.declarante,
        incluir_aportes=not args.sin_aportes,
    )

    print()
    generar_resumen(resultado)

    if resultado["aportes"] and resultado["aportes"]["nota_minimo"]:
        print(f"\n⚠  {resultado['aportes']['nota_minimo']}\n")


if __name__ == "__main__":
    main()
