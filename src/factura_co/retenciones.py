"""
retenciones.py — Cálculo de retención en la fuente para Colombia 2024.

Basado en el Estatuto Tributario colombiano, artículos 392 a 401, y las
resoluciones de la DIAN vigentes para 2024.

La retención en la fuente es un mecanismo de recaudo anticipado del impuesto
de renta. El pagador (cliente) retiene un porcentaje del valor pagado al
beneficiario (freelancer) y lo consigna a la DIAN.

Referencia:
    - Artículo 392 ET: Retención en honorarios y servicios
    - Decreto 2418 de 2013 (tarifas base)
    - UVT 2024: $47.065 (Resolución DIAN 000187 de 2023)
"""

from typing import Literal

# Valor de la UVT para 2024
UVT_2024 = 47_065

# Tipos de servicio soportados
TipoServicio = Literal[
    "honorarios",
    "servicios",
    "arrendamiento",
    "compras",
    "transporte",
]

# Tabla de retenciones en la fuente (tarifa declarante / tarifa no declarante)
# Formato: {tipo: (tarifa_declarante, tarifa_no_declarante, base_minima_uvt)}
TABLA_RETENCIONES = {
    "honorarios": {
        "declarante": 0.10,       # 10% para declarantes de renta
        "no_declarante": 0.11,    # 11% para no declarantes
        "base_minima_uvt": 0,     # Sin base mínima (aplica desde el primer peso)
        "descripcion": "Honorarios, comisiones y servicios técnicos y científicos",
        "articulo_et": "Art. 392",
    },
    "servicios": {
        "declarante": 0.04,       # 4% para declarantes
        "no_declarante": 0.06,    # 6% para no declarantes
        "base_minima_uvt": 4,     # Aplica si el valor >= 4 UVT ($188.260 en 2024)
        "descripcion": "Servicios en general (diseño, consultoría, etc.)",
        "articulo_et": "Art. 392",
    },
    "arrendamiento": {
        "declarante": 0.035,      # 3.5% para bienes muebles
        "no_declarante": 0.035,   # Misma tarifa independiente de declaración
        "base_minima_uvt": 0,
        "descripcion": "Arrendamiento de bienes muebles",
        "articulo_et": "Art. 401",
    },
    "compras": {
        "declarante": 0.025,      # 2.5% para declarantes
        "no_declarante": 0.035,   # 3.5% para no declarantes
        "base_minima_uvt": 27,    # Aplica si el valor >= 27 UVT ($1.270.755 en 2024)
        "descripcion": "Compras en general de bienes o productos",
        "articulo_et": "Art. 401",
    },
    "transporte": {
        "declarante": 0.035,      # 3.5% para declarantes
        "no_declarante": 0.035,   # Misma tarifa
        "base_minima_uvt": 27,    # Aplica si el valor >= 27 UVT
        "descripcion": "Servicios de transporte nacional",
        "articulo_et": "Art. 401",
    },
}


def calcular_retencion(
    valor: float,
    tipo_servicio: TipoServicio = "honorarios",
    es_declarante: bool = False,
    uvt: int = UVT_2024,
) -> dict:
    """
    Calcula la retención en la fuente para un pago a un freelancer colombiano.

    Args:
        valor: Valor bruto del servicio o factura en pesos colombianos.
        tipo_servicio: Tipo de servicio prestado. Opciones:
            - "honorarios": servicios profesionales y técnicos (más común para freelancers)
            - "servicios": servicios en general
            - "arrendamiento": arriendo de bienes muebles
            - "compras": compra de bienes
            - "transporte": servicios de transporte
        es_declarante: True si el beneficiario declara renta (generalmente
            aplica si ingresos anuales > 1.400 UVT ≈ $65.8M en 2024).
            Por defecto False (más conservador para freelancers nuevos).
        uvt: Valor de la UVT vigente. Por defecto UVT_2024 ($47.065).

    Returns:
        Diccionario con:
            - valor_bruto: valor original
            - tarifa: porcentaje aplicado (ej. 0.11)
            - tarifa_pct: porcentaje en formato legible (ej. "11.0%")
            - valor_retencion: monto retenido en pesos
            - valor_neto: lo que el cliente efectivamente paga/transfiere
            - tipo_servicio: tipo usado en el cálculo
            - aplica: bool indicando si aplica retención según base mínima
            - base_minima: monto mínimo desde el que aplica retención

    Raises:
        ValueError: Si el tipo_servicio no es válido o el valor es negativo.

    Examples:
        >>> # Honorarios por $3.000.000 (no declarante)
        >>> r = calcular_retencion(3_000_000, "honorarios")
        >>> r["valor_retencion"]
        330000.0
        >>> r["tarifa_pct"]
        '11.0%'

        >>> # Servicio por $500.000 (debajo de base mínima: 4 UVT = $188.260)
        >>> r = calcular_retencion(500_000, "servicios")
        >>> r["aplica"]
        True
        >>> r["valor_retencion"]
        30000.0
    """
    if valor < 0:
        raise ValueError(f"El valor no puede ser negativo: {valor}")

    if tipo_servicio not in TABLA_RETENCIONES:
        tipos_validos = list(TABLA_RETENCIONES.keys())
        raise ValueError(
            f"Tipo de servicio '{tipo_servicio}' no válido. "
            f"Opciones: {tipos_validos}"
        )

    config = TABLA_RETENCIONES[tipo_servicio]
    tarifa = config["declarante"] if es_declarante else config["no_declarante"]
    base_minima_pesos = config["base_minima_uvt"] * uvt

    # Verificar si aplica retención según base mínima
    aplica = valor >= base_minima_pesos

    if aplica:
        valor_retencion = round(valor * tarifa)
    else:
        valor_retencion = 0

    return {
        "valor_bruto": valor,
        "tarifa": tarifa,
        "tarifa_pct": f"{tarifa * 100:.1f}%",
        "valor_retencion": float(valor_retencion),
        "valor_neto": valor - valor_retencion,
        "tipo_servicio": tipo_servicio,
        "descripcion_tipo": config["descripcion"],
        "aplica": aplica,
        "base_minima_uvt": config["base_minima_uvt"],
        "base_minima_pesos": base_minima_pesos,
        "es_declarante": es_declarante,
        "articulo_et": config["articulo_et"],
    }


def listar_tipos_servicio() -> dict:
    """
    Retorna información sobre todos los tipos de servicio disponibles.

    Returns:
        Diccionario con información de cada tipo de servicio.

    Examples:
        >>> tipos = listar_tipos_servicio()
        >>> "honorarios" in tipos
        True
    """
    return {
        tipo: {
            "descripcion": config["descripcion"],
            "tarifa_declarante": f"{config['declarante'] * 100:.1f}%",
            "tarifa_no_declarante": f"{config['no_declarante'] * 100:.1f}%",
            "base_minima_uvt": config["base_minima_uvt"],
            "articulo_et": config["articulo_et"],
        }
        for tipo, config in TABLA_RETENCIONES.items()
    }
