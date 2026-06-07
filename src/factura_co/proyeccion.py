"""
proyeccion.py — Proyección anual de ingresos para freelancers colombianos.

Dado un ingreso mensual promedio en USD o COP, proyecta:
  - Ingreso bruto anual
  - Retenciones anuales (acumuladas por mes)
  - Aportes obligatorios (salud + pensión)
  - Renta liquida gravable estimada
  - Impuesto de renta aproximado
  - Neto disponible real anual y mensual promedio
  - Ahorro mínimo recomendado para cubrir obligaciones
"""

from __future__ import annotations
import math
from .retenciones import calcular_retencion, TipoServicio
from .aportes import calcular_aportes


# Rangos impuesto de renta 2024 (UVT base 47.065 COP)
# Fuente: Estatuto Tributario Art. 241, valores en UVT
TABLA_RENTA_UVT = [
    # (limite_inferior_uvt, limite_superior_uvt, tasa, uvt_exceso_base)
    (0,     1090,  0.000, 0),
    (1090,  1700,  0.190, 1090),
    (1700,  4100,  0.280, 1700),
    (4100,  8670,  0.330, 4100),
    (8670,  18970, 0.350, 8670),
    (18970, math.inf, 0.390, 18970),
]

UVT_2024 = 47_065.0  # COP


def calcular_impuesto_renta(renta_liquida_cop: float) -> dict:
    """
    Calcula el impuesto de renta aproximado para una renta líquida dada.

    Nota: Es un estimado simplificado. Para declaración real consultar
    contador o usar el formulario 210 de la DIAN.

    Args:
        renta_liquida_cop: Renta líquida gravable en COP.

    Returns:
        dict con: renta_liquida, renta_uvt, impuesto_cop, tasa_efectiva_pct.
    """
    renta_uvt = renta_liquida_cop / UVT_2024
    impuesto_uvt = 0.0

    for lim_inf, lim_sup, tasa, base in TABLA_RENTA_UVT:
        if renta_uvt <= lim_inf:
            break
        exceso_uvt = min(renta_uvt, lim_sup) - lim_inf
        impuesto_uvt += exceso_uvt * tasa

    impuesto_cop = impuesto_uvt * UVT_2024
    tasa_efectiva = (impuesto_cop / renta_liquida_cop * 100) if renta_liquida_cop > 0 else 0

    return {
        "renta_liquida_cop": round(renta_liquida_cop),
        "renta_uvt": round(renta_uvt, 2),
        "impuesto_cop": round(impuesto_cop),
        "tasa_efectiva_pct": round(tasa_efectiva, 2),
        "uvt_2024": UVT_2024,
    }


def proyeccion_anual(
    ingreso_mensual_cop: float,
    tipo_servicio: str = "honorarios",
    es_declarante: bool = True,
    incluir_aportes: bool = True,
    meses: int = 12,
) -> dict:
    """
    Proyecta el ingreso real anual considerando todas las obligaciones.

    Args:
        ingreso_mensual_cop: Ingreso mensual bruto promedio en COP.
        tipo_servicio: Tipo de servicio para calcular retención.
        es_declarante: True si declara renta (afecta tasa de retención).
        incluir_aportes: True para incluir salud y pensión.
        meses: Número de meses a proyectar (defecto 12).

    Returns:
        dict con desglose completo anual y promedio mensual.

    Examples:
        >>> r = proyeccion_anual(5_000_000)
        >>> r["ingreso_bruto_anual"] == 60_000_000
        True
        >>> r["neto_anual"] > 0
        True
    """
    ingreso_bruto_anual = ingreso_mensual_cop * meses

    # Acumular mes a mes
    total_retenciones = 0.0
    total_aportes = 0.0

    for _ in range(meses):
        ret = calcular_retencion(ingreso_mensual_cop, tipo_servicio, es_declarante)
        total_retenciones += ret["valor_retencion"]

        if incluir_aportes:
            ap = calcular_aportes(ingreso_mensual_cop)
            total_aportes += ap["total_aportes"]

    ingreso_recibido_anual = ingreso_bruto_anual - total_retenciones

    # Renta líquida estimada: ingresos - aportes (deducibles)
    renta_liquida = max(0, ingreso_bruto_anual - total_aportes)
    impuesto_info = calcular_impuesto_renta(renta_liquida)
    impuesto_renta = impuesto_info["impuesto_cop"]

    # Las retenciones se descuentan del impuesto a pagar
    saldo_renta = max(0, impuesto_renta - total_retenciones)

    neto_anual = ingreso_bruto_anual - total_aportes - impuesto_renta
    neto_mensual_prom = neto_anual / meses if meses > 0 else 0

    # Ahorro mensual recomendado para cubrir obligaciones no retenidas
    ahorro_recomendado_mensual = (total_aportes + saldo_renta) / meses if meses > 0 else 0

    return {
        # Ingresos
        "ingreso_mensual_bruto": ingreso_mensual_cop,
        "meses_proyectados": meses,
        "ingreso_bruto_anual": round(ingreso_bruto_anual),
        # Retenciones
        "total_retenciones_anual": round(total_retenciones),
        "ingreso_recibido_anual": round(ingreso_recibido_anual),
        # Aportes
        "total_aportes_anual": round(total_aportes),
        "incluye_aportes": incluir_aportes,
        # Renta
        "renta_liquida_estimada": round(renta_liquida),
        "impuesto_renta_estimado": round(impuesto_renta),
        "tasa_renta_efectiva_pct": impuesto_info["tasa_efectiva_pct"],
        "saldo_a_pagar_renta": round(saldo_renta),
        # Neto final
        "neto_anual": round(neto_anual),
        "neto_mensual_promedio": round(neto_mensual_prom),
        "neto_pct_bruto": round((neto_anual / ingreso_bruto_anual) * 100, 2) if ingreso_bruto_anual > 0 else 0,
        # Recomendaciones
        "ahorro_mensual_recomendado": round(ahorro_recomendado_mensual),
        # Parámetros usados
        "tipo_servicio": tipo_servicio,
        "es_declarante": es_declarante,
    }


def proyeccion_desde_usd(
    ingreso_mensual_usd: float,
    trm: float,
    plataforma: str = "wise",
    tipo_servicio: str = "honorarios",
    es_declarante: bool = True,
    meses: int = 12,
) -> dict:
    """
    Proyección anual a partir de ingresos en USD, aplicando comisión de plataforma.

    Args:
        ingreso_mensual_usd: Ingreso mensual en USD.
        trm: TRM COP/USD.
        plataforma: Plataforma de cobro para aplicar comisiones.
        tipo_servicio: Tipo de servicio para retención.
        es_declarante: True si declara renta.
        meses: Meses a proyectar.

    Returns:
        Proyección anual con ingreso_cop_neto_plataforma adicional.

    Examples:
        >>> r = proyeccion_desde_usd(1000, 4200, "wise")
        >>> r["ingreso_bruto_anual"] > 0
        True
    """
    from .plataformas import calcular_neto_plataforma

    # Calcular neto COP después de comisiones de plataforma (mensual)
    resultado_plat = calcular_neto_plataforma(ingreso_mensual_usd, plataforma, trm)
    ingreso_cop_mensual = resultado_plat["valor_cop"]

    # Proyección completa en COP
    proy = proyeccion_anual(
        ingreso_cop_mensual,
        tipo_servicio=tipo_servicio,
        es_declarante=es_declarante,
        meses=meses,
    )

    proy["ingreso_mensual_usd"] = ingreso_mensual_usd
    proy["trm_usada"] = trm
    proy["plataforma_cobro"] = resultado_plat["plataforma"]
    proy["comision_plataforma_mensual_usd"] = resultado_plat["comision_usd"]
    proy["comision_plataforma_anual_cop"] = round(
        resultado_plat["comision_usd"] * resultado_plat["trm_efectiva"] * meses
    )

    return proy


def resumen_proyeccion(proy: dict) -> str:
    """
    Genera texto resumen legible de la proyección anual.

    Args:
        proy: Resultado de proyeccion_anual() o proyeccion_desde_usd().

    Returns:
        String formateado para consola o app.
    """
    sep = "=" * 65
    lineas = [
        sep,
        "    PROYECCIÓN ANUAL — factura-co",
        sep,
        f"  Meses proyectados:      {proy['meses_proyectados']}",
        f"  Ingreso mensual bruto:  ${proy['ingreso_mensual_bruto']:>15,.0f} COP",
        "",
        f"  INGRESO BRUTO ANUAL:    ${proy['ingreso_bruto_anual']:>15,.0f} COP",
        f"  (-) Aportes SS:        -${proy['total_aportes_anual']:>15,.0f} COP",
        f"  (-) Impuesto de renta: -${proy['impuesto_renta_estimado']:>15,.0f} COP",
        f"       Tasa efectiva:     {proy['tasa_renta_efectiva_pct']:>14.1f}%",
        "",
        f"  {'='*45}",
        f"  NETO DISPONIBLE ANUAL:  ${proy['neto_anual']:>15,.0f} COP",
        f"  Promedio mensual:       ${proy['neto_mensual_promedio']:>15,.0f} COP",
        f"  % del bruto:            {proy['neto_pct_bruto']:>14.1f}%",
        "",
        f"  Ahorro mensual recomendado:",
        f"  (aportes + diferencia renta): ${proy['ahorro_mensual_recomendado']:>12,.0f} COP",
        sep,
        "  * Estimado. Consulte un contador para su declaración real.",
        sep,
    ]
    return "\n".join(lineas)
