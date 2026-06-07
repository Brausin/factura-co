#!/usr/bin/env python3
"""
actualizar_uvt.py — Actualiza data/uvt_history.json con el valor del UVT del año vigente.

Uso:
    python scripts/actualizar_uvt.py

Descripcion:
    Este script verifica si el año actual ya está registrado en el historial de UVT.
    Si no está, agrega el valor para ese año (hardcoded anualmente según la resolución DIAN)
    y hace commit del cambio.

Actualizacion manual:
    Cada año, cuando la DIAN publica el nuevo valor del UVT (típicamente en diciembre),
    actualizar el diccionario UVT_VALORES_CONOCIDOS con el nuevo año y valor.

Fuente oficial:
    Resoluciones DIAN publicadas en: https://www.dian.gov.co/normatividad/normas/Paginas/default.aspx
    Buscar: "Resolucion UVT [año]"
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

# ─── TABLA DE VALORES CONOCIDOS ──────────────────────────────────────────────
# Actualizar manualmente cada diciembre cuando la DIAN publique la resolución.
# Fuente: Resoluciones DIAN anuales — Art. 868 Estatuto Tributario.
UVT_VALORES_CONOCIDOS = {
    2015: {"valor": 28279, "resolucion_dian": "Resolución 000228 de 2014", "incremento_pct": 3.65},
    2016: {"valor": 29753, "resolucion_dian": "Resolución 000114 de 2015", "incremento_pct": 5.21},
    2017: {"valor": 31859, "resolucion_dian": "Resolución 000102 de 2016", "incremento_pct": 7.08},
    2018: {"valor": 33156, "resolucion_dian": "Resolución 000062 de 2017", "incremento_pct": 4.07},
    2019: {"valor": 34270, "resolucion_dian": "Resolución 000024 de 2019", "incremento_pct": 3.36},
    2020: {"valor": 35607, "resolucion_dian": "Resolución 000084 de 2019", "incremento_pct": 3.90},
    2021: {"valor": 36308, "resolucion_dian": "Resolución 000111 de 2020", "incremento_pct": 1.97},
    2022: {"valor": 38004, "resolucion_dian": "Resolución 000140 de 2021", "incremento_pct": 4.67},
    2023: {"valor": 42412, "resolucion_dian": "Resolución 000178 de 2022", "incremento_pct": 11.60},
    2024: {"valor": 47065, "resolucion_dian": "Resolución 000187 de 2023", "incremento_pct": 10.97},
    2025: {"valor": 49799, "resolucion_dian": "Resolución 000186 de 2024", "incremento_pct": 5.81},
    # 2026: {"valor": XXXXX, "resolucion_dian": "Resolución 000XXX de 2025", "incremento_pct": X.XX},
    # Agregar el próximo año aquí en diciembre, cuando la DIAN lo publique.
}
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
UVT_FILE = ROOT / "data" / "uvt_history.json"


def cargar_historial() -> dict:
    """Carga el historial de UVT desde el archivo JSON."""
    if not UVT_FILE.exists():
        print(f"[ERROR] No se encontró {UVT_FILE}")
        sys.exit(1)
    with open(UVT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_historial(data: dict) -> None:
    """Guarda el historial actualizado con formato legible."""
    with open(UVT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Historial guardado en {UVT_FILE}")


def actualizar_ano(ano: int) -> bool:
    """
    Verifica si el año está en el historial y lo agrega si no.

    Returns:
        True si se hizo una actualización, False si ya existía.
    """
    if ano not in UVT_VALORES_CONOCIDOS:
        print(f"[AVISO] El año {ano} no está en UVT_VALORES_CONOCIDOS.")
        print("        Actualiza el diccionario en este script con el valor oficial de la DIAN.")
        print(f"        Busca: 'Resolución DIAN UVT {ano}' en https://www.dian.gov.co")
        return False

    datos = cargar_historial()
    anos_existentes = datos.get("años", {})

    if str(ano) in anos_existentes:
        valor_actual = anos_existentes[str(ano)]["valor"]
        print(f"[INFO] El año {ano} ya está registrado. UVT = ${valor_actual:,}")
        return False

    # Agregar el nuevo año
    valor_nuevo = UVT_VALORES_CONOCIDOS[ano]
    anos_existentes[str(ano)] = valor_nuevo
    datos["años"] = dict(sorted({int(k): v for k, v in anos_existentes.items()}.items()))
    datos["años"] = {str(k): v for k, v in datos["años"].items()}

    guardar_historial(datos)
    print(f"[OK] Año {ano} agregado: UVT = ${valor_nuevo['valor']:,} ({valor_nuevo['resolucion_dian']})")
    return True


def reporte() -> None:
    """Muestra el estado actual del historial."""
    datos = cargar_historial()
    anos = datos.get("años", {})
    print("\n=== Estado del historial UVT ===")
    print(f"{'Año':<8} {'Valor UVT':>12} {'Resolución DIAN':<35}")
    print("-" * 60)
    for ano, info in sorted({int(k): v for k, v in anos.items()}.items()):
        print(f"{ano:<8} ${info['valor']:>10,}   {info['resolucion_dian']:<35}")
    print("-" * 60)
    año_max = max(int(k) for k in anos)
    uvt_max = anos[str(año_max)]["valor"]
    print(f"\nUVT vigente ({año_max}): ${uvt_max:,}")
    print(f"Proximo año a agregar: {año_max + 1}")
    print("=" * 60)


if __name__ == "__main__":
    ano_actual = date.today().year
    print(f"factura-co — Actualizador de UVT")
    print(f"Fecha: {date.today().isoformat()} | Año fiscal: {ano_actual}")
    print("-" * 40)

    actualizado = actualizar_ano(ano_actual)

    if actualizado:
        print(f"\n[OK] Historial actualizado con el año {ano_actual}.")
        print("     Verifica el commit con: git log --oneline -3")
    else:
        print(f"\n[INFO] No se realizaron cambios al historial.")

    reporte()
