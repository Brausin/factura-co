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


def calcular_bruto_necesario(
    neto_cop_deseado: float,
    tipo_servicio: str = "honorarios",
    es_declarante: bool = False,
    incluir_aportes: bool = True,
    plataforma: str | None = None,
    trm: float | None = None,
    tipo_upwork: str = "nuevo",
    tolerancia: float = 1.0,
    max_iter: int = 100,
) -> dict:
    """
    Calcula el valor bruto que debes facturar para recibir un neto específico.

    Resuelve la ecuación inversa de calcular_neto() por aproximaciones sucesivas
    (búsqueda binaria), ya que retenciones y aportes no son lineales.

    Si se pasa 'plataforma' y 'trm', también incluye las comisiones de la
    plataforma en el cálculo (cuánto debe pagarte el cliente para que TÚ
    recibas neto_cop_deseado después de todo).

    Args:
        neto_cop_deseado: COP que quieres recibir neto al final.
        tipo_servicio: Tipo de servicio para retención.
        es_declarante: True si declaras renta.
        incluir_aportes: True para incluir salud y pensión.
        plataforma: Si aplica, plataforma de cobro para incluir comisión.
        trm: TRM necesaria si se pasa plataforma.
        tipo_upwork: Tramo Upwork si aplica.
        tolerancia: Diferencia máxima aceptable en COP (default 1).
        max_iter: Máximo de iteraciones de búsqueda binaria.

    Returns:
        dict con: neto_deseado, bruto_necesario, diferencia_real, desglose_completo,
                  bruto_usd_necesario (si se usó plataforma).

    Raises:
        ValueError: Si el neto deseado es negativo o mayor al límite posible.

    Examples:
        >>> r = calcular_bruto_necesario(3_000_000, "honorarios")
        >>> r["bruto_necesario"] > 3_000_000
        True

        >>> # Recibir $3M neto después de retención + aportes
        >>> r = calcular_bruto_necesario(3_000_000)
        >>> abs(r["neto_real"] - 3_000_000) < 100
        True
    """
    if neto_cop_deseado <= 0:
        raise ValueError("El neto deseado debe ser positivo.")

    # Búsqueda binaria para encontrar el bruto
    lo = neto_cop_deseado       # mínimo posible (si retención fuera 0%)
    hi = neto_cop_deseado * 4   # máximo generous (retención máxima ~75% teórico)

    bruto_optimo = hi
    desglose_optimo = None

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        desglose = calcular_neto(
            mid, tipo_servicio, es_declarante, incluir_aportes
        )
        neto_actual = desglose["neto"]
        diff = neto_actual - neto_cop_deseado

        if abs(diff) <= tolerancia:
            bruto_optimo = mid
            desglose_optimo = desglose
            break

        if diff < 0:
            lo = mid
        else:
            hi = mid
            bruto_optimo = mid
            desglose_optimo = desglose

    if desglose_optimo is None:
        desglose_optimo = calcular_neto(bruto_optimo, tipo_servicio, es_declarante, incluir_aportes)

    resultado = {
        "neto_deseado": neto_cop_deseado,
        "bruto_necesario": round(bruto_optimo),
        "neto_real": round(desglose_optimo["neto"]),
        "diferencia": round(desglose_optimo["neto"] - neto_cop_deseado),
        "desglose": desglose_optimo,
        "tiene_plataforma": False,
    }

    # Si se especificó plataforma, calcular cuánto debe enviar el cliente en USD
    if plataforma and trm:
        from .plataformas import calcular_neto_plataforma
        # Buscar el USD bruto que después de comisiones deja el COP bruto necesario
        # cop_neto_plataforma = usd * (1 - comision%) * (1 - spread%) * trm
        # usd_bruto = bruto_cop / ((1 - comision_pct) * (1 - spread_fx) * trm)
        # Aproximación directa (suficientemente precisa para valores razonables)
        lo_usd = bruto_optimo / (trm * 1.1)
        hi_usd = bruto_optimo / (trm * 0.5)
        bruto_usd = hi_usd
        plat_desglose = None

        for _ in range(max_iter):
            mid_usd = (lo_usd + hi_usd) / 2
            plat_r = calcular_neto_plataforma(mid_usd, plataforma, trm, tipo_upwork)
            cop_plat = plat_r["valor_cop"]
            diff = cop_plat - bruto_optimo

            if abs(diff) <= tolerancia:
                bruto_usd = mid_usd
                plat_desglose = plat_r
                break

            if diff < 0:
                lo_usd = mid_usd
            else:
                hi_usd = mid_usd
                bruto_usd = mid_usd
                plat_desglose = plat_r

        resultado["tiene_plataforma"] = True
        resultado["plataforma"] = plataforma
        resultado["bruto_usd_necesario"] = round(bruto_usd, 2)
        resultado["desglose_plataforma"] = plat_desglose

    return resultado
