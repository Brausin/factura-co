#!/usr/bin/env python3
"""
calcular.py — CLI para calcular retenciones y aportes desde la terminal.

Uso:
    python calcular.py --valor 3000000 --tipo honorarios
    python calcular.py --valor 5000000 --tipo servicios --declarante
    python calcular.py --valor 2000000 --tipo honorarios --sin-aportes
    python calcular.py --valor 3000000 --exportar
    python calcular.py --valor 3000000 --documento
    python calcular.py --listar-tipos
    python calcular.py --version
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

# Agregar la raíz del proyecto al path para importar factura_co
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.factura_co.calculadora import calcular_neto
    from src.factura_co.retenciones import listar_tipos_servicio, obtener_uvt
    from src.factura_co.documento import generar_documento_txt, guardar_documento
    from src.factura_co import __version__
except ImportError:
    from factura_co.calculadora import calcular_neto
    from factura_co.retenciones import listar_tipos_servicio, obtener_uvt
    from factura_co.documento import generar_documento_txt, guardar_documento
    from factura_co import __version__

try:
    from tabulate import tabulate
    _TABULATE_OK = True
except ImportError:
    _TABULATE_OK = False


# ── Helpers de formato ────────────────────────────────────────────────────────

def _fmt(valor: float, signo: str = "") -> str:
    """Formatea un número como pesos colombianos."""
    return f"{signo}${valor:>14,.0f}"


def _tabla(filas: list, headers: list, fmt: str = "fancy_grid") -> str:
    """Genera tabla con tabulate o fallback ASCII."""
    if _TABULATE_OK:
        return tabulate(filas, headers=headers, tablefmt=fmt, colalign=("left", "right"))
    # Fallback sin tabulate
    sep = "-" * 50
    lines = [sep]
    lines.append(f"  {headers[0]:<30} {headers[1]:>14}")
    lines.append(sep)
    for fila in filas:
        lines.append(f"  {str(fila[0]):<30} {str(fila[1]):>14}")
    lines.append(sep)
    return "\n".join(lines)


# ── Tablas de presentación ────────────────────────────────────────────────────

def imprimir_tabla_tipos():
    """Imprime tabla de tipos de servicio disponibles."""
    tipos = listar_tipos_servicio()
    uvt = obtener_uvt()

    filas = []
    for tipo, info in tipos.items():
        filas.append([
            tipo,
            info["descripcion"][:38],
            info["tarifa_no_declarante"],
            info["tarifa_declarante"],
            f"{info['base_minima_uvt']} UVT" if info["base_minima_uvt"] > 0 else "Sin mínimo",
        ])

    headers = ["Tipo", "Descripción", "No decl.", "Declarante", "Base mínima"]
    print()
    print(f"  TIPOS DE SERVICIO — UVT vigente: ${uvt:,}")
    print()
    if _TABULATE_OK:
        print(tabulate(filas, headers=headers, tablefmt="fancy_grid"))
    else:
        print(f"  {'Tipo':<15} {'No decl.':>9} {'Declarante':>10} {'Base mínima':>12}")
        print("  " + "-" * 52)
        for f in filas:
            print(f"  {f[0]:<15} {f[2]:>9} {f[3]:>10} {f[4]:>12}")
    print()
    print("  Nota: 'Declarante' aplica si tus ingresos anuales superan ~1.400 UVT")
    print()


def imprimir_resultado(resultado: dict, valor: float, tipo: str, declarante: bool):
    """Imprime el desglose del resultado en tabla formateada."""
    ret = resultado["retencion"]
    aportes = resultado["aportes"]

    filas_ret = [
        ["Valor bruto de la factura", _fmt(valor)],
        [f"Retención en la fuente ({ret['tarifa_pct']})", _fmt(resultado["valor_retenido"], "-")],
        ["Valor que transfiere el cliente", _fmt(resultado["valor_recibido"])],
    ]

    print()
    print("  RETENCIÓN EN LA FUENTE")
    print(_tabla(filas_ret, ["Concepto", "Valor (COP)"]))

    if resultado["incluye_aportes"] and aportes:
        a = aportes
        filas_ap = [
            [f"IBC (40% del ingreso bruto)", _fmt(a["ibc"])],
            [f"Aporte a salud (12.5% del IBC)", _fmt(a["aporte_salud"], "-")],
            [f"Aporte a pensión (16% del IBC)", _fmt(a["aporte_pension"], "-")],
            ["Total aportes a pagar", _fmt(a["total_aportes"], "-")],
        ]
        print()
        print("  APORTES A SEGURIDAD SOCIAL")
        print(_tabla(filas_ap, ["Concepto", "Valor (COP)"]))

        if a["nota_minimo"]:
            print(f"\n  ⚠  {a['nota_minimo']}")

    # Neto final destacado
    neto = resultado["neto"]
    neto_pct = resultado["neto_pct"]
    print()
    if _TABULATE_OK:
        fila_neto = [["INGRESO NETO REAL", _fmt(neto), f"({neto_pct:.1f}% del bruto)"]]
        print(tabulate(fila_neto, tablefmt="double_outline"))
    else:
        print(f"  {'=' * 50}")
        print(f"  INGRESO NETO REAL: {_fmt(neto)}  ({neto_pct:.1f}%)")
        print(f"  {'=' * 50}")
    print()

    cond = "declarante" if declarante else "no declarante"
    uvt = ret.get("uvt_usado", obtener_uvt())
    print(f"  Tipo: {tipo} · Condición fiscal: {cond} · UVT usado: ${uvt:,}")
    print()


# ── Exportar a JSON ───────────────────────────────────────────────────────────

def exportar_json(resultado: dict, valor: float, tipo: str) -> str:
    """
    Guarda el resultado en ~/factura-co-resultados/<timestamp>.json.

    Returns:
        Ruta del archivo guardado.
    """
    directorio = Path.home() / "factura-co-resultados"
    directorio.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"calculo_{tipo}_{ts}.json"
    ruta = directorio / nombre

    # Serializar resultado (convertir floats y tipos no serializables)
    datos = {
        "fecha_calculo": datetime.now().isoformat(),
        "valor_factura": valor,
        "tipo_servicio": tipo,
        "valor_retenido": resultado["valor_retenido"],
        "valor_recibido": resultado["valor_recibido"],
        "total_aportes": resultado["total_aportes"],
        "neto": resultado["neto"],
        "neto_pct": resultado["neto_pct"],
        "retencion": {
            k: v for k, v in resultado["retencion"].items()
        },
        "aportes": (
            {k: v for k, v in resultado["aportes"].items() if k != "ibc_info"}
            if resultado["aportes"] else None
        ),
    }

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, default=str)

    return str(ruta)


# ── Generar documento TXT ─────────────────────────────────────────────────────

def generar_documento_interactivo(valor: float, tipo: str) -> str:
    """
    Solicita los datos necesarios y genera el documento de cobro en TXT.

    Returns:
        Ruta del archivo generado.
    """
    print()
    print("  ── DATOS PARA EL DOCUMENTO DE COBRO ──────────────────")
    print("  (Presiona Enter para dejar en blanco los campos opcionales)")
    print()

    nombre = input("  Tu nombre completo: ").strip()
    if not nombre:
        print("  ❌ El nombre es obligatorio.")
        sys.exit(1)

    cedula = input("  Tu cédula o NIT: ").strip()
    if not cedula:
        print("  ❌ La cédula es obligatoria.")
        sys.exit(1)

    ciudad = input("  Tu ciudad [Bogotá]: ").strip() or "Bogotá"
    banco = input("  Banco (opcional): ").strip()
    cuenta = input("  Número de cuenta (opcional): ").strip()
    tipo_cuenta = input("  Tipo de cuenta (Ahorros/Corriente) [Ahorros]: ").strip() or "Ahorros"

    print()
    empresa = input("  Empresa cliente (razón social): ").strip()
    if not empresa:
        print("  ❌ La razón social del cliente es obligatoria.")
        sys.exit(1)

    nit_cliente = input("  NIT del cliente: ").strip()
    if not nit_cliente:
        print("  ❌ El NIT del cliente es obligatorio.")
        sys.exit(1)

    descripcion = input("  Descripción del servicio: ").strip()
    if not descripcion:
        descripcion = f"Prestación de servicios de {tipo}"

    freelancer = {
        "nombre": nombre,
        "cedula": cedula,
        "ciudad": ciudad,
    }
    if banco:
        freelancer["banco"] = banco
    if cuenta:
        freelancer["cuenta"] = cuenta
        freelancer["tipo_cuenta"] = tipo_cuenta

    cliente = {
        "empresa": empresa,
        "nit": nit_cliente,
    }

    contenido = generar_documento_txt(
        datos_freelancer=freelancer,
        datos_cliente=cliente,
        valor=valor,
        descripcion=descripcion,
        incluir_retencion=True,
    )

    directorio = Path.home() / "factura-co-resultados"
    directorio.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"cuenta_cobro_{nombre.split()[0].lower()}_{ts}.txt"
    ruta = directorio / nombre_archivo

    guardar_documento(contenido, str(ruta))
    return str(ruta)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="factura-co: Calculadora de retenciones y aportes para freelancers colombianos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python calcular.py --valor 3000000 --tipo honorarios
  python calcular.py --valor 5000000 --tipo servicios --declarante
  python calcular.py --valor 3000000 --exportar
  python calcular.py --valor 3000000 --documento
  python calcular.py --listar-tipos
  python calcular.py --version
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
        "--exportar",
        action="store_true",
        default=False,
        help="Guardar resultado en JSON en ~/factura-co-resultados/",
    )
    parser.add_argument(
        "--documento",
        action="store_true",
        default=False,
        help="Generar cuenta de cobro en TXT (solicita datos interactivamente)",
    )
    parser.add_argument(
        "--listar-tipos",
        action="store_true",
        default=False,
        help="Mostrar tabla de tipos de servicio y tarifas",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"factura-co {__version__}",
        help="Mostrar versión del paquete",
    )

    args = parser.parse_args()

    if args.listar_tipos:
        imprimir_tabla_tipos()
        return

    if args.valor is None:
        parser.print_help()
        print("\n  ❌  Falta el argumento --valor. Ejemplo: --valor 3000000\n")
        sys.exit(1)

    # Validaciones de entrada
    if args.valor < 0:
        print(
            f"\n  ❌  El valor no puede ser negativo (recibido: ${args.valor:,.0f}).\n"
            "      Ingresa el valor bruto de tu factura en pesos colombianos.\n"
        )
        sys.exit(1)

    if args.valor == 0:
        print(
            "\n  ❌  El valor debe ser mayor a cero.\n"
            "      Ingresa el valor bruto de tu factura en pesos colombianos.\n"
        )
        sys.exit(1)

    if args.valor < 10_000:
        print(
            f"\n  ⚠   Valor muy bajo: ${args.valor:,.0f}. "
            "¿Lo ingresaste en pesos colombianos?\n"
            "      Ejemplo para $3.000.000: --valor 3000000\n"
        )

    # Cálculo
    try:
        resultado = calcular_neto(
            valor_factura=args.valor,
            tipo_servicio=args.tipo,
            es_declarante=args.declarante,
            incluir_aportes=not args.sin_aportes,
        )
    except ValueError as e:
        print(f"\n  ❌  Error en el cálculo: {e}\n")
        sys.exit(1)

    # Mostrar resultado
    imprimir_resultado(resultado, args.valor, args.tipo, args.declarante)

    # Exportar JSON
    if args.exportar:
        ruta = exportar_json(resultado, args.valor, args.tipo)
        print(f"  ✅  Resultado guardado en: {ruta}\n")

    # Generar documento TXT
    if args.documento:
        ruta = generar_documento_interactivo(args.valor, args.tipo)
        print(f"\n  ✅  Documento guardado en: {ruta}\n")


if __name__ == "__main__":
    main()
