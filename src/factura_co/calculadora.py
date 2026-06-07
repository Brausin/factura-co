"""
calculadora.py — Módulo principal de factura-co.

Combina el cálculo de retenciones y aportes en un único desglose
del ingreso neto real para un freelancer colombiano.
"""

from .retenciones import calcular_retencion, TipoServicio
from .aportes import calcular_aportes


def calcular_neto(
    valor_factura: float,
    tipo_servicio: TipoServicio = "honorarios",
    es_declarante: bool = False,
    incluir_aportes: bool = True,
) -> dict:
    """
    Calcula el ingreso neto real de una factura para un freelancer colombiano.

    Combina la retención en la fuente y los aportes obligatorios a seguridad
    social para mostrar cuánto dinero queda disponible realmente.

    Args:
        valor_factura: Valor bruto de la factura en pesos colombianos.
        tipo_servicio: Tipo de servicio (ver retenciones.TABLA_RETENCIONES).
        es_declarante: True si el beneficiario declara renta. Por defecto False.
        incluir_aportes: True para incluir salud y pensión en el cálculo.
            False si ya tienes plan de salud por otro medio o quieres
            solo ver la retención.

    Returns:
        Diccionario con:
            - valor_factura: valor original
            - retencion: resultado completo de calcular_retencion()
            - valor_retenido: monto retenido
            - valor_recibido: lo que el cliente transfiere
            - aportes: resultado de calcular_aportes() (o None si incluir_aportes=False)
            - total_aportes: monto total a pagar a SGSS
            - neto: ingreso disponible final
            - neto_pct: porcentaje del bruto que queda como neto
            - incluye_aportes: bool

    Raises:
        ValueError: Si el valor es negativo o el tipo de servicio no es válido.

    Examples:
        >>> # Honorarios por $3.000.000
        >>> r = calcular_neto(3_000_000, "honorarios")
        >>> r["neto"]
        1957500
        >>> r["neto_pct"]
        65.25

        >>> # Solo retención, sin aportes
        >>> r = calcular_neto(3_000_000, "honorarios", incluir_aportes=False)
        >>> r["neto"]
        2670000
    """
    if valor_factura <= 0:
        raise ValueError(f"El valor de la factura debe ser positivo: {valor_factura}")

    # Calcular retención
    retencion = calcular_retencion(valor_factura, tipo_servicio, es_declarante)
    valor_recibido = retencion["valor_neto"]

    # Calcular aportes sobre el ingreso bruto
    aportes = None
    total_aportes = 0
    if incluir_aportes:
        aportes = calcular_aportes(valor_factura)
        total_aportes = aportes["total_aportes"]

    neto = valor_recibido - total_aportes
    neto_pct = round((neto / valor_factura) * 100, 2)

    return {
        "valor_factura": valor_factura,
        "retencion": retencion,
        "valor_retenido": retencion["valor_retencion"],
        "valor_recibido": valor_recibido,
        "aportes": aportes,
        "total_aportes": total_aportes,
        "neto": neto,
        "neto_pct": neto_pct,
        "incluye_aportes": incluir_aportes,
    }


def generar_resumen(resultado: dict) -> str:
    """
    Genera e imprime un resumen legible del desglose de ingreso.

    Args:
        resultado: Diccionario retornado por calcular_neto().

    Returns:
        String con el resumen formateado (también lo imprime en consola).

    Examples:
        >>> r = calcular_neto(3_000_000, "honorarios")
        >>> texto = generar_resumen(r)
        >>> "INGRESO NETO REAL" in texto
        True
    """
    sep = "=" * 60
    linea = "-" * 42

    vf = f"${resultado['valor_factura']:,.0f}"
    ret = resultado["retencion"]
    vret = f"-${resultado['valor_retenido']:,.0f}"
    vrec = f"${resultado['valor_recibido']:,.0f}"
    vneto = f"${resultado['neto']:,.0f}"

    lineas = [
        sep,
        "        DESGLOSE DE INGRESO - factura-co",
        sep,
        f"  Valor factura:       {vf:>20}",
        f"  Retención ({ret['tarifa_pct']}):    {vret:>20}",
        f"  Valor a recibir:     {vrec:>20}",
    ]

    if resultado["incluye_aportes"] and resultado["aportes"]:
        a = resultado["aportes"]
        vibc = f"${a['ibc']:,.0f}"
        vsalud = f"-${a['aporte_salud']:,.0f}"
        vpension = f"-${a['aporte_pension']:,.0f}"
        vtotal = f"-${a['total_aportes']:,.0f}"
        lineas.append("")
        lineas.append(f"  Base cotización (40%): {vibc:>18}")
        lineas.append(f"  Aporte salud (12.5%):  {vsalud:>18}")
        lineas.append(f"  Aporte pensión (16%):  {vpension:>18}")
        lineas.append(f"  Total aportes:         {vtotal:>18}")
        if a["nota_minimo"]:
            lineas.append(f"  Nota: {a['nota_minimo']}")

    lineas.append("")
    lineas.append(f"  {linea}")
    lineas.append(f"  INGRESO NETO REAL:   {vneto:>20}")
    lineas.append(f"  (equivale al {resultado['neto_pct']:.1f}% del valor facturado)")
    lineas.append(sep)

    texto = "\n".join(lineas)
    print(texto)
    return texto
