"""
cli.py — Interfaz de línea de comandos de factura-co.

Permite usar la calculadora directamente desde la terminal:

    factura-co neto 3000000                      # neto de una factura
    factura-co neto 3000000 --tipo servicios --declarante
    factura-co bruto 3000000                     # cuánto facturar para ese neto
    factura-co comparar 1000                     # ranking de plataformas (TRM en vivo)
    factura-co comparar 1000 --trm 4200
    factura-co trm                               # TRM vigente con fuente
    factura-co tipos                             # tipos de servicio y tarifas

Cada subcomando acepta --json para salida en formato JSON.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .calculadora import calcular_bruto_necesario, calcular_neto, generar_resumen
from .comparador import comparar_plataformas, tabla_comparacion
from .retenciones import TABLA_RETENCIONES, listar_tipos_servicio
from .trm_live import get_trm_hoy, get_trm_info

_TIPOS = sorted(TABLA_RETENCIONES.keys())


def _imprimir_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _cmd_neto(args: argparse.Namespace) -> int:
    resultado = calcular_neto(
        args.valor,
        tipo_servicio=args.tipo,
        es_declarante=args.declarante,
        incluir_aportes=not args.sin_aportes,
    )
    if args.json:
        _imprimir_json(resultado)
    else:
        generar_resumen(resultado)
    return 0


def _cmd_bruto(args: argparse.Namespace) -> int:
    resultado = calcular_bruto_necesario(
        args.neto,
        tipo_servicio=args.tipo,
        es_declarante=args.declarante,
        incluir_aportes=not args.sin_aportes,
        plataforma=args.plataforma,
        trm=args.trm,
    )
    if args.json:
        resultado = dict(resultado)
        resultado.pop("desglose", None)
        resultado.pop("desglose_plataforma", None)
        _imprimir_json(resultado)
    else:
        print(f"Neto deseado:     ${resultado['neto_deseado']:,.0f} COP")
        print(f"Debes facturar:   ${resultado['bruto_necesario']:,.0f} COP")
        print(f"Neto real:        ${resultado['neto_real']:,.0f} COP")
        if resultado.get("tiene_plataforma"):
            print(
                f"El cliente debe enviar: USD {resultado['bruto_usd_necesario']:,.2f} "
                f"vía {resultado['plataforma']}"
            )
    return 0


def _cmd_comparar(args: argparse.Namespace) -> int:
    trm = args.trm if args.trm else get_trm_hoy()
    if args.json:
        _imprimir_json(comparar_plataformas(args.usd, trm, args.upwork))
    else:
        print(tabla_comparacion(args.usd, trm, args.upwork, top_n=args.top))
    return 0


def _cmd_trm(args: argparse.Namespace) -> int:
    info = get_trm_info()
    if args.json:
        _imprimir_json(info)
    else:
        print(f"TRM hoy: ${info['trm']:,.2f} COP/USD")
        print(f"Fuente:  {info['fuente']}")
        if info["es_estimado"]:
            print("Aviso:   valor estimado (sin conexión a fuentes en vivo)")
    return 0


def _cmd_tipos(args: argparse.Namespace) -> int:
    tipos = listar_tipos_servicio()
    if args.json:
        _imprimir_json(tipos)
    else:
        for tipo, info in tipos.items():
            print(f"\n{tipo}  ({info['articulo_et']})")
            print(f"  {info['descripcion']}")
            print(
                f"  Tarifa declarante: {info['tarifa_declarante']} | "
                f"no declarante: {info['tarifa_no_declarante']}"
            )
            print(
                f"  Base mínima: {info['base_minima_uvt']} UVT "
                f"(${info['base_minima_pesos']:,.0f})"
            )
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="factura-co",
        description="Calculadora financiera para freelancers colombianos.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    # neto
    p_neto = sub.add_parser("neto", help="Neto real de una factura en COP")
    p_neto.add_argument("valor", type=float, help="Valor bruto de la factura (COP)")
    p_neto.add_argument("--tipo", default="honorarios", choices=_TIPOS)
    p_neto.add_argument("--declarante", action="store_true",
                        help="El beneficiario declara renta")
    p_neto.add_argument("--sin-aportes", action="store_true",
                        help="No incluir aportes a salud y pensión")
    p_neto.add_argument("--json", action="store_true", help="Salida en JSON")
    p_neto.set_defaults(func=_cmd_neto)

    # bruto
    p_bruto = sub.add_parser(
        "bruto", help="Cuánto facturar para recibir un neto específico"
    )
    p_bruto.add_argument("neto", type=float, help="Neto deseado (COP)")
    p_bruto.add_argument("--tipo", default="honorarios", choices=_TIPOS)
    p_bruto.add_argument("--declarante", action="store_true")
    p_bruto.add_argument("--sin-aportes", action="store_true")
    p_bruto.add_argument("--plataforma", default=None,
                         help="Incluir comisión de plataforma (wise, paypal, ...)")
    p_bruto.add_argument("--trm", type=float, default=None,
                         help="TRM a usar si se indica plataforma")
    p_bruto.add_argument("--json", action="store_true")
    p_bruto.set_defaults(func=_cmd_bruto)

    # comparar
    p_comp = sub.add_parser("comparar", help="Ranking de plataformas de pago")
    p_comp.add_argument("usd", type=float, help="Monto en USD a recibir")
    p_comp.add_argument("--trm", type=float, default=None,
                        help="TRM a usar (por defecto, TRM en vivo)")
    p_comp.add_argument("--upwork", default="nuevo",
                        choices=["nuevo", "medio", "senior"])
    p_comp.add_argument("--top", type=int, default=None,
                        help="Mostrar solo las N mejores")
    p_comp.add_argument("--json", action="store_true")
    p_comp.set_defaults(func=_cmd_comparar)

    # trm
    p_trm = sub.add_parser("trm", help="TRM vigente con fuente")
    p_trm.add_argument("--json", action="store_true")
    p_trm.set_defaults(func=_cmd_trm)

    # tipos
    p_tipos = sub.add_parser("tipos", help="Tipos de servicio y tarifas de retención")
    p_tipos.add_argument("--json", action="store_true")
    p_tipos.set_defaults(func=_cmd_tipos)

    return parser


def main(argv=None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
