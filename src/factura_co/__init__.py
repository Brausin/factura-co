"""
factura-co: Suite financiera completa para freelancers colombianos.

Calcula retenciones, aportes, compara plataformas de pago internacionales,
genera documentos de cobro y proyecta ingresos anuales.

Módulos:
    - retenciones: retefuente (Estatuto Tributario), ICA, historial UVT
    - aportes: salud 12.5%, pensión 16%, IBC
    - calculadora: cálculo integrado neto + calculadora inversa
    - plataformas: comisiones PayPal, Wise, Payoneer, Upwork, Freelancer, Binance, etc.
    - comparador: tabla comparativa de plataformas ordenada por neto COP
    - trm_live: TRM en tiempo real con fallback automático
    - proyeccion: proyección anual de ingresos con impuesto de renta
    - documento: cuenta de cobro en TXT
    - documento_pdf: cuenta de cobro en PDF (requiere fpdf2)
"""

__version__ = "0.3.0"
__author__ = "Brausin"
__license__ = "MIT"

from .calculadora import calcular_neto, generar_resumen, calcular_bruto_necesario
from .retenciones import calcular_retencion, calcular_ica, obtener_uvt
from .aportes import calcular_aportes, ingreso_base_cotizacion
from .plataformas import calcular_neto_plataforma, listar_plataformas
from .comparador import comparar_plataformas, tabla_comparacion, mejor_plataforma
from .trm_live import get_trm_hoy, get_trm_info
from .proyeccion import proyeccion_anual, proyeccion_desde_usd, resumen_proyeccion

__all__ = [
    # Calculadora principal
    "calcular_neto",
    "generar_resumen",
    "calcular_bruto_necesario",
    # Retenciones y aportes
    "calcular_retencion",
    "calcular_ica",
    "obtener_uvt",
    "calcular_aportes",
    "ingreso_base_cotizacion",
    # Plataformas de pago
    "calcular_neto_plataforma",
    "listar_plataformas",
    "comparar_plataformas",
    "tabla_comparacion",
    "mejor_plataforma",
    # TRM en tiempo real
    "get_trm_hoy",
    "get_trm_info",
    # Proyección anual
    "proyeccion_anual",
    "proyeccion_desde_usd",
    "resumen_proyeccion",
]
