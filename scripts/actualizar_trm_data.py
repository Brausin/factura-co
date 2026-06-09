"""
actualizar_trm_data.py — Actualiza el histórico diario de TRM.

Pensado para ejecutarse desde un GitHub Action (ver
``.github/workflows/actualizar_trm.yml``). Descarga la TRM vigente y agrega una
fila al archivo ``data/trm_historico.csv`` solo si la fecha de hoy aún no está
registrada, de modo que el commit diario sea idempotente.

Fuentes (en orden de preferencia):
  1. datos.gov.co — Superintendencia Financiera (TRM oficial).
  2. exchangerate-api.com — tasa USD/COP de respaldo.

Se ejecuta de forma autónoma; solo requiere ``requests`` y ``pandas``.

    python scripts/actualizar_trm_data.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# El histórico vive junto a los demás datos del paquete.
_CSV = Path(__file__).resolve().parent.parent / "data" / "trm_historico.csv"
_COLUMNAS = ["fecha", "trm", "fuente"]
_TIMEOUT = 12


def fetch_datos_gov() -> tuple[float, str] | None:
    """TRM oficial vigente desde datos.gov.co (Superintendencia Financiera)."""
    url = (
        "https://www.datos.gov.co/resource/32sa-8pi3.json"
        "?$order=vigenciadesde DESC&$limit=1"
    )
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data and "valor" in data[0]:
            return round(float(data[0]["valor"]), 2), "datos.gov.co"
    except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
        print(f"  · datos.gov.co no disponible: {exc}")
    return None


def fetch_exchangerate() -> tuple[float, str] | None:
    """Tasa USD/COP de respaldo desde exchangerate-api.com."""
    try:
        resp = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=_TIMEOUT
        )
        resp.raise_for_status()
        cop = resp.json().get("rates", {}).get("COP")
        if cop:
            return round(float(cop), 2), "exchangerate-api.com"
    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f"  · exchangerate-api no disponible: {exc}")
    return None


def obtener_trm() -> tuple[float, str]:
    """Devuelve (trm, fuente) probando las fuentes en orden."""
    for fetch in (fetch_datos_gov, fetch_exchangerate):
        resultado = fetch()
        if resultado is not None:
            return resultado
    raise RuntimeError("No fue posible obtener la TRM de ninguna fuente.")


def cargar_historico() -> pd.DataFrame:
    """Lee el CSV histórico o crea uno vacío con la estructura esperada."""
    if _CSV.exists():
        df = pd.read_csv(_CSV, dtype={"fecha": str})
        # Asegura las columnas esperadas aunque el archivo sea antiguo.
        for col in _COLUMNAS:
            if col not in df.columns:
                df[col] = pd.NA
        return df[_COLUMNAS]
    return pd.DataFrame(columns=_COLUMNAS)


def main() -> None:
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    trm, fuente = obtener_trm()
    print(f"TRM obtenida: ${trm:,.2f} COP/USD ({fuente}) para {hoy}")

    df = cargar_historico()
    if hoy in set(df["fecha"].astype(str)):
        print(f"La fecha {hoy} ya está registrada; no se agregan filas.")
        return

    fila = pd.DataFrame([{"fecha": hoy, "trm": trm, "fuente": fuente}])
    df = pd.concat([df, fila], ignore_index=True)
    df = df.sort_values("fecha").reset_index(drop=True)
    _CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(_CSV, index=False)
    print(f"Fila agregada. El histórico tiene ahora {len(df)} registros.")
    print(f"Archivo: {_CSV.relative_to(_CSV.parent.parent)}")


if __name__ == "__main__":
    main()
