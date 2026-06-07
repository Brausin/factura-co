"""
factura-co: Calculadora de retenciones, aportes y generador de documentos
de cobro para freelancers e independientes colombianos.

Uso basico:
    from factura_co.calculadora import calcular_neto, generar_resumen

    resultado = calcular_neto(3_000_000, "honorarios")
    generar_resumen(resultado)

Modulos disponibles:
    - retenciones: retefuente, ICA, historial UVT
    - aportes: salud, pension, IBC
    - calculadora: calculo integrado neto
    - documento: cuenta de cobro en TXT
    - documento_pdf: cuenta de cobro en PDF (requiere fpdf2)
"""

__version__ = "0.2.0"
__author__ = "Brausin"
__license__ = "MIT"

from .calculadora import calcular_neto, generar_resumen
from .retenciones import calcular_retencion, calcular_ica, obtener_uvt
from .aportes import calcular_aportes, ingreso_base_cotizacion

__all__ = [
    "calcular_neto",
    "generar_resumen",
    "calcular_retencion",
    "calcular_ica",
    "obtener_uvt",
    "calcular_aportes",
    "ingreso_base_cotizacion",
]
