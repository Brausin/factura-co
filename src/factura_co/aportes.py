"""
aportes.py — Cálculo de aportes a salud y pensión para independientes (2024).

Los trabajadores independientes en Colombia deben cotizar al Sistema General
de Seguridad Social (SGSS) de manera autónoma. La base de cotización es el
40% del valor mensual facturado (Ingreso Base de Cotización, IBC).

Marco legal:
    - Ley 1607 de 2012, Art. 26: IBC para independientes = 40% del ingreso
    - Ley 1955 de 2019: Piso de protección social
    - Decreto 1601 de 2022: Reglamentación para independientes por contrato
    - Circular 01 de 2023 UGPP: Tarifas y procedimientos

Tarifas 2024:
    - Salud: 12.5% del IBC (empleador: 8.5% + empleado: 4% — para independientes, pago total)
    - Pensión: 16% del IBC (empleador: 12% + empleado: 4% — para independientes, pago total)
    - IBC mínimo: 1 SMMLV = $1.300.000 (2024)
    - IBC máximo: 25 SMMLV = $32.500.000 (2024)
"""

# Salario Mínimo Mensual Legal Vigente 2024
SMMLV_2024 = 1_300_000

# IBC mínimo: 1 SMMLV
IBC_MINIMO = SMMLV_2024

# IBC máximo: 25 SMMLV
IBC_MAXIMO = SMMLV_2024 * 25

# Tarifas de cotización para independientes
TARIFA_SALUD = 0.125    # 12.5%
TARIFA_PENSION = 0.16   # 16%
PORCENTAJE_IBC = 0.40   # 40% del ingreso bruto


def ingreso_base_cotizacion(ingreso_bruto: float) -> dict:
    """
    Calcula el Ingreso Base de Cotización (IBC) para un independiente.

    El IBC es la base sobre la que se calculan los aportes a salud y pensión.
    Para trabajadores independientes, equivale al 40% del ingreso mensual bruto,
    con un mínimo de 1 SMMLV y un máximo de 25 SMMLV.

    Args:
        ingreso_bruto: Ingreso bruto mensual en pesos colombianos.

    Returns:
        Diccionario con:
            - ingreso_bruto: ingreso recibido
            - ibc_calculado: 40% del ingreso bruto
            - ibc_aplicado: IBC real (ajustado por mínimo/máximo)
            - ibc_minimo: piso del IBC (1 SMMLV)
            - ibc_maximo: techo del IBC (25 SMMLV)
            - ajuste_aplicado: "ninguno", "minimo" o "maximo"

    Raises:
        ValueError: Si el ingreso es negativo.

    Examples:
        >>> ibc = ingreso_base_cotizacion(3_000_000)
        >>> ibc["ibc_aplicado"]
        1300000
        >>> ibc["ajuste_aplicado"]
        'minimo'

        >>> ibc = ingreso_base_cotizacion(5_000_000)
        >>> ibc["ibc_aplicado"]
        2000000
        >>> ibc["ajuste_aplicado"]
        'ninguno'
    """
    if ingreso_bruto < 0:
        raise ValueError(f"El ingreso no puede ser negativo: {ingreso_bruto}")

    ibc_calculado = ingreso_bruto * PORCENTAJE_IBC

    # Aplicar piso y techo
    if ibc_calculado < IBC_MINIMO:
        ibc_aplicado = IBC_MINIMO
        ajuste = "minimo"
    elif ibc_calculado > IBC_MAXIMO:
        ibc_aplicado = IBC_MAXIMO
        ajuste = "maximo"
    else:
        ibc_aplicado = ibc_calculado
        ajuste = "ninguno"

    return {
        "ingreso_bruto": ingreso_bruto,
        "ibc_calculado": round(ibc_calculado),
        "ibc_aplicado": round(ibc_aplicado),
        "ibc_minimo": IBC_MINIMO,
        "ibc_maximo": IBC_MAXIMO,
        "porcentaje_ibc": PORCENTAJE_IBC,
        "ajuste_aplicado": ajuste,
    }


def calcular_aportes(ingreso_mensual: float) -> dict:
    """
    Calcula los aportes a salud y pensión para un trabajador independiente.

    Para un freelancer que factura irregularmente, "ingreso mensual" debe
    entenderse como el ingreso del mes en que se realiza el pago. Si el
    contrato es de duración determinada, puede distribuirse el valor entre
    los meses del contrato.

    Args:
        ingreso_mensual: Valor total facturado en el mes (pesos colombianos).

    Returns:
        Diccionario con desglose completo de aportes:
            - ingreso_mensual: ingreso base
            - ibc_info: resultado de ingreso_base_cotizacion()
            - ibc: IBC aplicado
            - aporte_salud: valor a pagar a salud
            - aporte_pension: valor a pagar a pensión
            - total_aportes: suma de salud + pensión
            - tarifa_salud: tarifa aplicada (12.5%)
            - tarifa_pension: tarifa aplicada (16%)
            - nota_minimo: advertencia si se aplicó IBC mínimo

    Examples:
        >>> # Freelancer con $3.000.000 en honorarios
        >>> a = calcular_aportes(3_000_000)
        >>> a["ibc"]
        1300000
        >>> a["aporte_salud"]
        162500
        >>> a["aporte_pension"]
        208000
        >>> a["total_aportes"]
        370500

        >>> # Freelancer con ingresos altos: $8.000.000
        >>> a = calcular_aportes(8_000_000)
        >>> a["ibc"]
        3200000
    """
    if ingreso_mensual < 0:
        raise ValueError(f"El ingreso mensual no puede ser negativo: {ingreso_mensual}")

    ibc_info = ingreso_base_cotizacion(ingreso_mensual)
    ibc = ibc_info["ibc_aplicado"]

    aporte_salud = round(ibc * TARIFA_SALUD)
    aporte_pension = round(ibc * TARIFA_PENSION)
    total_aportes = aporte_salud + aporte_pension

    nota_minimo = None
    if ibc_info["ajuste_aplicado"] == "minimo":
        nota_minimo = (
            f"El IBC calculado ({ibc_info['ibc_calculado']:,.0f}) es menor al mínimo "
            f"(1 SMMLV = {IBC_MINIMO:,.0f}). Se usa el mínimo."
        )

    return {
        "ingreso_mensual": ingreso_mensual,
        "ibc_info": ibc_info,
        "ibc": ibc,
        "aporte_salud": aporte_salud,
        "aporte_pension": aporte_pension,
        "total_aportes": total_aportes,
        "tarifa_salud": TARIFA_SALUD,
        "tarifa_pension": TARIFA_PENSION,
        "porcentaje_ibc": PORCENTAJE_IBC,
        "nota_minimo": nota_minimo,
    }
