"""
comparador.py — Comparador de plataformas de pago para freelancers colombianos.

Muestra cuánto recibirías en COP al cobrar un valor determinado en USD
a través de distintas plataformas, ordenado de mayor a menor neto.
"""

from __future__ import annotations
from .plataformas import calcular_neto_plataforma, COMISIONES


def comparar_plataformas(
    valor_usd: float,
    trm: float,
    tipo_upwork: str = "nuevo",
) -> list[dict]:
    """
    Compara todas las plataformas para un valor dado en USD.

    Args:
        valor_usd: Monto en USD que el cliente pagará.
        trm: Tasa de cambio USD/COP.
        tipo_upwork: Tramo de Upwork ('nuevo'/'medio'/'senior').

    Returns:
        Lista ordenada de mayor a menor neto COP, con posición de ranking.

    Examples:
        >>> resultados = comparar_plataformas(1000, 4100)
        >>> resultados[0]["posicion"] == 1
        True
        >>> len(resultados) == len(COMISIONES)
        True
    """
    resultados = []
    for plataforma_id in COMISIONES:
        kwarg = {}
        if plataforma_id == "upwork":
            kwarg["tipo_upwork"] = tipo_upwork
        r = calcular_neto_plataforma(valor_usd, plataforma_id, trm, **kwarg)
        resultados.append(r)

    resultados.sort(key=lambda x: x["valor_cop"], reverse=True)

    for i, r in enumerate(resultados, 1):
        r["posicion"] = i

    return resultados


def tabla_comparacion(
    valor_usd: float,
    trm: float,
    tipo_upwork: str = "nuevo",
    top_n: int | None = None,
) -> str:
    """
    Genera una tabla de texto para mostrar la comparación en consola o app.

    Args:
        valor_usd: Monto USD a comparar.
        trm: TRM USD/COP.
        tipo_upwork: Tramo Upwork.
        top_n: Si se especifica, muestra solo las N mejores opciones.

    Returns:
        String con la tabla formateada.

    Examples:
        >>> tabla = tabla_comparacion(1000, 4100)
        >>> "Wise" in tabla
        True
        >>> "POSICIÓN" in tabla
        True
    """
    resultados = comparar_plataformas(valor_usd, trm, tipo_upwork)
    if top_n:
        resultados = resultados[:top_n]

    sep = "=" * 72
    encabezado = (
        f"{'POS':<4} {'PLATAFORMA':<22} {'USD NETO':>10} "
        f"{'COMISIÓN':>10} {'COP NETO':>14} {'% COSTO':>8}"
    )
    linea_sep = "-" * 72

    lineas = [
        sep,
        f"  COMPARADOR DE PLATAFORMAS — ${valor_usd:,.0f} USD  |  TRM: ${trm:,.0f}",
        sep,
        encabezado,
        linea_sep,
    ]

    mejor_cop = resultados[0]["valor_cop"] if resultados else 0

    for r in resultados:
        diff = r["valor_cop"] - mejor_cop
        diff_str = f"(-${abs(diff):,.0f})" if diff < 0 else "  ✓ mejor"
        lineas.append(
            f"#{r['posicion']:<3} {r['plataforma']:<22} "
            f"${r['valor_usd_neto']:>8,.2f}  "
            f"-${r['comision_usd']:>7,.2f}  "
            f"${r['valor_cop']:>12,.0f}  "
            f"{r['costo_total_pct']:>6.1f}%  {diff_str}"
        )

    lineas.append(sep)
    lineas.append(
        f"  Ahorros máximos vs peor opción: "
        f"${resultados[0]['valor_cop'] - resultados[-1]['valor_cop']:,.0f} COP"
    )
    lineas.append(sep)

    return "\n".join(lineas)


def mejor_plataforma(valor_usd: float, trm: float, tipo_upwork: str = "nuevo") -> dict:
    """
    Retorna solo la mejor plataforma para recibir un monto dado.

    Examples:
        >>> mejor = mejor_plataforma(1000, 4100)
        >>> "plataforma" in mejor
        True
    """
    resultados = comparar_plataformas(valor_usd, trm, tipo_upwork)
    return resultados[0] if resultados else {}


def peor_plataforma(valor_usd: float, trm: float, tipo_upwork: str = "nuevo") -> dict:
    """Retorna la plataforma con mayor costo (la que deja menos COP)."""
    resultados = comparar_plataformas(valor_usd, trm, tipo_upwork)
    return resultados[-1] if resultados else {}
