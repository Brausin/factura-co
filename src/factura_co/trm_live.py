"""
trm_live.py — TRM en tiempo real para factura-co.

Obtiene la tasa de cambio USD/COP vigente del día usando múltiples
fuentes con fallback automático:
  1. API pública de datos.gov.co (Superintendencia Financiera)
  2. API de exchangerate-api.com (free tier)
  3. Valor de respaldo hardcoded (actualizado periódicamente)

Para uso en producción, importa get_trm_hoy() directamente.
"""

from __future__ import annotations
import datetime
import json
import os
import urllib.request

# Valor de respaldo — se actualiza con GitHub Actions
_TRM_FALLBACK = 4_150.0
_TRM_FALLBACK_FECHA = "2025-01-15"


def _fetch_trm_datos_gov() -> float | None:
    """Consulta la API oficial de datos.gov.co (Superfinanciera)."""
    try:
        url = (
            "https://www.datos.gov.co/resource/32sa-8pi3.json"
            "?$order=vigenciadesde DESC&$limit=1"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            if data and "valor" in data[0]:
                return float(data[0]["valor"])
    except Exception:
        pass
    return None


def _fetch_trm_exchangerate() -> float | None:
    """Consulta exchangerate-api.com como segunda fuente."""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            cop = data.get("rates", {}).get("COP")
            if cop:
                return float(cop)
    except Exception:
        pass
    return None


def _fetch_trm_frankfurter() -> float | None:
    """Consulta frankfurter.app como tercera fuente."""
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=COP"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            cop = data.get("rates", {}).get("COP")
            if cop:
                return float(cop)
    except Exception:
        pass
    return None


def get_trm_hoy(verbose: bool = False) -> float:
    """
    Retorna la TRM (USD/COP) vigente del día con fallback automático.

    Intenta 3 fuentes en orden de prioridad. Si todas fallan, retorna
    el valor hardcoded de respaldo.

    Args:
        verbose: Si True, imprime la fuente usada.

    Returns:
        TRM en COP por 1 USD (ej: 4200.5)

    Examples:
        >>> trm = get_trm_hoy()
        >>> 3000 < trm < 6000  # rango razonable COP/USD
        True
    """
    fuentes = [
        ("datos.gov.co (Superfinanciera)", _fetch_trm_datos_gov),
        ("exchangerate-api.com", _fetch_trm_exchangerate),
        ("frankfurter.app", _fetch_trm_frankfurter),
    ]

    for nombre, fn in fuentes:
        valor = fn()
        if valor and 2_000 < valor < 8_000:  # rango de seguridad COP/USD
            if verbose:
                print(f"TRM obtenida de {nombre}: ${valor:,.2f} COP/USD")
            return valor

    if verbose:
        print(f"TRM de respaldo (hardcoded): ${_TRM_FALLBACK:,.2f} COP/USD")
    return _TRM_FALLBACK


def get_trm_info() -> dict:
    """
    Retorna TRM con metadata sobre la fuente y fecha.

    Returns:
        dict con: trm, fecha_consulta, fuente, es_estimado
    """
    fuentes_info = [
        ("datos.gov.co (Superfinanciera)", _fetch_trm_datos_gov),
        ("exchangerate-api.com", _fetch_trm_exchangerate),
        ("frankfurter.app", _fetch_trm_frankfurter),
    ]

    hoy = datetime.date.today().isoformat()

    for nombre, fn in fuentes_info:
        valor = fn()
        if valor and 2_000 < valor < 8_000:
            return {
                "trm": valor,
                "fecha_consulta": hoy,
                "fuente": nombre,
                "es_estimado": False,
            }

    return {
        "trm": _TRM_FALLBACK,
        "fecha_consulta": hoy,
        "fuente": f"Respaldo hardcoded (ref: {_TRM_FALLBACK_FECHA})",
        "es_estimado": True,
    }


if __name__ == "__main__":
    info = get_trm_info()
    print(f"TRM hoy: ${info['trm']:,.2f} COP/USD")
    print(f"Fuente: {info['fuente']}")
    print(f"Estimado: {info['es_estimado']}")
