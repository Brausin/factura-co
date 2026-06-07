"""
retenciones.py — Cálculo de retención en la fuente e ICA para Colombia.

Basado en el Estatuto Tributario colombiano, artículos 392 a 401, y las
resoluciones de la DIAN vigentes. El historial de UVT se carga desde
data/uvt_history.json para mantener los valores actualizados año a año.

Referencias:
    - Artículo 392 ET: Retención en honorarios y servicios
    - Artículo 401 ET: Retención en compras y arrendamiento
    - Decreto 2418 de 2013 (tarifas base)
    - Artículo 33 Ley 14 de 1983: ICA (Impuesto de Industria y Comercio)
    - Acuerdo 65 de 2002 (tarifas ICA Bogotá)
"""

import json
import os
from typing import Literal, Optional

# ── Carga del historial de UVT ────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_UVT_FILE = os.path.join(_DATA_DIR, "uvt_history.json")

def _cargar_uvt_history() -> dict:
    """Carga el historial de UVT desde data/uvt_history.json."""
    ruta = os.path.normpath(_UVT_FILE)
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {int(año): info["valor"] for año, info in data["años"].items()}
    # Fallback con valores hardcoded si no se encuentra el archivo
    return {
        2015: 28279, 2016: 29753, 2017: 31859, 2018: 33156, 2019: 34270,
        2020: 35607, 2021: 36308, 2022: 38004, 2023: 42412, 2024: 47065,
        2025: 49799,
    }

UVT_HISTORY = _cargar_uvt_history()

# UVT vigente (año más reciente disponible)
UVT_VIGENTE = UVT_HISTORY[max(UVT_HISTORY.keys())]

# Mantener alias del año 2024 para retrocompatibilidad
UVT_2024 = UVT_HISTORY.get(2024, 47065)


def obtener_uvt(año: Optional[int] = None) -> int:
    """
    Retorna el valor de la UVT para un año dado.

    Args:
        año: Año fiscal. Si es None, retorna el UVT vigente (año más reciente).

    Returns:
        Valor de la UVT en pesos colombianos.

    Raises:
        ValueError: Si el año solicitado no está en el historial.

    Examples:
        >>> obtener_uvt(2024)
        47065
        >>> obtener_uvt(2023)
        42412
        >>> obtener_uvt()  # año más reciente
        49799
    """
    if año is None:
        return UVT_VIGENTE
    if año not in UVT_HISTORY:
        años_disponibles = sorted(UVT_HISTORY.keys())
        raise ValueError(
            f"Año {año} no disponible. Años con datos: {años_disponibles[0]}–{años_disponibles[-1]}"
        )
    return UVT_HISTORY[año]


# ── Tipos de servicio ─────────────────────────────────────────────────────────
TipoServicio = Literal[
    "honorarios",
    "servicios",
    "arrendamiento",
    "compras",
    "transporte",
]

# Tabla de retenciones en la fuente (tarifa declarante / tarifa no declarante)
# Formato: {tipo: {declarante, no_declarante, base_minima_uvt, descripcion, articulo_et}}
TABLA_RETENCIONES = {
    "honorarios": {
        "declarante": 0.10,
        "no_declarante": 0.11,
        "base_minima_uvt": 0,
        "descripcion": "Honorarios, comisiones y servicios técnicos y científicos",
        "articulo_et": "Art. 392",
    },
    "servicios": {
        "declarante": 0.04,
        "no_declarante": 0.06,
        "base_minima_uvt": 4,
        "descripcion": "Servicios en general (diseño, consultoría, etc.)",
        "articulo_et": "Art. 392",
    },
    "arrendamiento": {
        "declarante": 0.035,
        "no_declarante": 0.035,
        "base_minima_uvt": 0,
        "descripcion": "Arrendamiento de bienes muebles o inmuebles",
        "articulo_et": "Art. 401",
    },
    "compras": {
        "declarante": 0.025,
        "no_declarante": 0.035,
        "base_minima_uvt": 27,
        "descripcion": "Compras en general de bienes o productos",
        "articulo_et": "Art. 401",
    },
    "transporte": {
        "declarante": 0.035,
        "no_declarante": 0.035,
        "base_minima_uvt": 27,
        "descripcion": "Servicios de transporte nacional",
        "articulo_et": "Art. 401",
    },
}

# ── Tarifas ICA por municipio (por mil — ‰) ───────────────────────────────────
# Fuente: estatutos tributarios municipales vigentes
# El ICA aplica sobre actividades comerciales, industriales y de servicios
# en la jurisdicción del municipio donde se ejecuta la actividad.
TARIFAS_ICA_POR_MIL = {
    "bogota": {
        "servicios_profesionales": 9.66,   # Acuerdo 65 de 2002, Bogotá
        "servicios_generales": 4.14,
        "comercio": 4.14,
        "industria": 4.14,
        "descripcion": "Bogotá D.C. — Acuerdo 65 de 2002",
    },
    "medellin": {
        "servicios_profesionales": 10.0,
        "servicios_generales": 5.0,
        "comercio": 5.0,
        "industria": 4.0,
        "descripcion": "Medellín — Estatuto Tributario Municipal",
    },
    "cali": {
        "servicios_profesionales": 9.0,
        "servicios_generales": 4.0,
        "comercio": 4.14,
        "industria": 3.0,
        "descripcion": "Cali — Acuerdo 0373 de 2014",
    },
    "barranquilla": {
        "servicios_profesionales": 8.0,
        "servicios_generales": 4.0,
        "comercio": 4.0,
        "industria": 3.0,
        "descripcion": "Barranquilla — Decreto 0212 de 2000",
    },
    "otro": {
        "servicios_profesionales": 5.0,
        "servicios_generales": 4.0,
        "comercio": 4.0,
        "industria": 3.0,
        "descripcion": "Municipio no listado — tarifa estimada (verificar estatuto local)",
    },
}


def calcular_retencion(
    valor: float,
    tipo_servicio: TipoServicio = "honorarios",
    es_declarante: bool = False,
    uvt: Optional[int] = None,
    año: Optional[int] = None,
) -> dict:
    """
    Calcula la retención en la fuente para un pago a un freelancer colombiano.

    Args:
        valor: Valor bruto del servicio o factura en pesos colombianos.
        tipo_servicio: Tipo de servicio prestado. Opciones:
            - "honorarios": servicios profesionales y técnicos
            - "servicios": servicios en general
            - "arrendamiento": arriendo de bienes muebles o inmuebles
            - "compras": compra de bienes
            - "transporte": servicios de transporte
        es_declarante: True si el beneficiario declara renta. Generalmente
            aplica si ingresos anuales > 1.400 UVT (~$69.7M en 2025).
        uvt: Valor explícito del UVT a usar. Si se omite, se usa el valor
            del año indicado en `año`, o el vigente si tampoco se especifica.
        año: Año fiscal para seleccionar el UVT correspondiente.

    Returns:
        Diccionario con desglose completo de la retención.

    Raises:
        ValueError: Si el valor es negativo o el tipo de servicio no existe.

    Examples:
        >>> r = calcular_retencion(3_000_000, "honorarios")
        >>> r["valor_retencion"]
        330000.0
        >>> r["tarifa_pct"]
        '11.0%'

        >>> # Usando UVT de 2024 explícitamente
        >>> r = calcular_retencion(500_000, "servicios", año=2024)
        >>> r["aplica"]
        True
    """
    if valor < 0:
        raise ValueError(
            f"El valor no puede ser negativo. Recibido: ${valor:,.0f}. "
            "Ingresa el valor bruto de la factura en pesos colombianos."
        )

    if tipo_servicio not in TABLA_RETENCIONES:
        tipos_validos = list(TABLA_RETENCIONES.keys())
        raise ValueError(
            f"Tipo de servicio '{tipo_servicio}' no válido. "
            f"Tipos válidos: {tipos_validos}. "
            "Usa --listar-tipos para ver la descripción de cada uno."
        )

    # Resolver UVT a usar
    if uvt is None:
        uvt = obtener_uvt(año)

    config = TABLA_RETENCIONES[tipo_servicio]
    tarifa = config["declarante"] if es_declarante else config["no_declarante"]
    base_minima_pesos = config["base_minima_uvt"] * uvt

    aplica = valor >= base_minima_pesos
    valor_retencion = round(valor * tarifa) if aplica else 0

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
        "uvt_usado": uvt,
    }


def calcular_ica(
    valor: float,
    municipio: str = "bogota",
    tipo_actividad: str = "servicios_profesionales",
    tarifa_por_mil_personalizada: Optional[float] = None,
) -> dict:
    """
    Calcula la ReteICA (retención del Impuesto de Industria y Comercio).

    El ICA es un impuesto municipal que grava las actividades comerciales,
    industriales y de servicios. Las empresas que pagan a proveedores de
    servicios actúan como agentes de retención del ICA.

    Marco legal:
        - Ley 14 de 1983, Art. 33: base del ICA
        - Cada municipio define su tarifa mediante acuerdo municipal
        - La retención es del 100% del ICA causado en la operación

    Args:
        valor: Valor bruto del servicio en pesos colombianos.
        municipio: Municipio donde se presta el servicio.
            Opciones: "bogota", "medellin", "cali", "barranquilla", "otro".
        tipo_actividad: Tipo de actividad económica.
            Opciones: "servicios_profesionales", "servicios_generales",
            "comercio", "industria".
        tarifa_por_mil_personalizada: Si se especifica, usa esta tarifa (‰)
            en lugar de la tabla de municipios.

    Returns:
        Diccionario con:
            - valor_bruto: valor base del cálculo
            - municipio: municipio usado
            - tipo_actividad: actividad económica
            - tarifa_por_mil: tarifa en por mil (‰)
            - tarifa_pct: tarifa en porcentaje
            - valor_ica: monto a retener por ICA
            - valor_neto: valor después de ICA
            - descripcion_fuente: referencia normativa

    Raises:
        ValueError: Si el valor es negativo o el municipio/actividad no existen.

    Examples:
        >>> ica = calcular_ica(3_000_000, "bogota", "servicios_profesionales")
        >>> ica["tarifa_por_mil"]
        9.66
        >>> ica["valor_ica"]
        28980
    """
    if valor < 0:
        raise ValueError(f"El valor no puede ser negativo: ${valor:,.0f}")

    municipio_lower = municipio.lower().strip()
    if municipio_lower not in TARIFAS_ICA_POR_MIL:
        municipios_validos = list(TARIFAS_ICA_POR_MIL.keys())
        raise ValueError(
            f"Municipio '{municipio}' no disponible. "
            f"Opciones: {municipios_validos}. "
            "Para otros municipios usa 'otro' y especifica la tarifa con "
            "tarifa_por_mil_personalizada."
        )

    info_municipio = TARIFAS_ICA_POR_MIL[municipio_lower]

    if tipo_actividad not in info_municipio:
        actividades_validas = [k for k in info_municipio if k != "descripcion"]
        raise ValueError(
            f"Tipo de actividad '{tipo_actividad}' no válido para {municipio}. "
            f"Opciones: {actividades_validas}"
        )

    if tarifa_por_mil_personalizada is not None:
        tarifa_pm = tarifa_por_mil_personalizada
    else:
        tarifa_pm = info_municipio[tipo_actividad]

    valor_ica = round(valor * tarifa_pm / 1000)

    return {
        "valor_bruto": valor,
        "municipio": municipio_lower,
        "tipo_actividad": tipo_actividad,
        "tarifa_por_mil": tarifa_pm,
        "tarifa_pct": f"{tarifa_pm / 10:.3f}%",
        "valor_ica": valor_ica,
        "valor_neto": valor - valor_ica,
        "descripcion_fuente": info_municipio["descripcion"],
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
    uvt_actual = obtener_uvt()
    return {
        tipo: {
            "descripcion": config["descripcion"],
            "tarifa_declarante": f"{config['declarante'] * 100:.1f}%",
            "tarifa_no_declarante": f"{config['no_declarante'] * 100:.1f}%",
            "base_minima_uvt": config["base_minima_uvt"],
            "base_minima_pesos": config["base_minima_uvt"] * uvt_actual,
            "articulo_et": config["articulo_et"],
        }
        for tipo, config in TABLA_RETENCIONES.items()
    }
