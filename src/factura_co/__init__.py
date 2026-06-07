"""
factura-co: Calculadora de retenciones, aportes y generador de documentos
de cobro para freelancers e independientes colombianos.

Uso básico:
    from factura_co.calculadora import calcular_neto, generar_resumen

    resultado = calcular_neto(3_000_000, "honorarios")
    generar_resumen(resultado)
"""

__version__ = "0.1.0"
__author__ = "Brausin"
__license__ = "MIT"

from .calculadora import calcular_neto, generar_resumen
from .retenciones import calcular_retencion
from .aportes import calcular_aportes, ingreso_base_cotizacion

__all__ = [
    "calcular_neto",
    "generar_resumen",
    "calcular_retencion",
    "calcular_aportes",
    "ingreso_base_cotizacion",
]
