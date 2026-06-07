"""
plataformas.py — Comisiones reales de plataformas de pago internacionales.

Cubre todos los canales por los que un freelancer colombiano puede recibir
pagos del exterior: PayPal, Wise, Payoneer, Upwork, Freelancer, Binance P2P,
Buda.com, SWIFT/bancario, Nequi internacional.

Fuentes verificadas (2024-2025):
  - PayPal: https://www.paypal.com/co/webapps/mpp/merchant-fees
  - Wise: https://wise.com/co/pricing/
  - Payoneer: https://www.payoneer.com/es/support/fees/
  - Upwork: https://support.upwork.com/hc/en-us/articles/211062538
  - Freelancer: https://www.freelancer.com/feeschedule.php
  - Binance P2P: spread de mercado ~1%, red cripto variable
  - Buda.com: https://buda.com/fees
  - SWIFT: comisión fija del banco emisor + receptor
  - Nequi Internacional: piloto con tarifas estimadas
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

PlataformaNombre = Literal[
    "paypal", "wise", "payoneer", "upwork", "freelancer",
    "binance", "buda", "swift", "nequi",
]
TipoUpwork = Literal["nuevo", "medio", "senior"]


@dataclass
class ComisionPlataforma:
    nombre: str
    porcentaje: float
    fijo_usd: float
    spread_fx: float
    descripcion: str
    fuente: str
    notas: list = field(default_factory=list)
    fijo_es_minimo: bool = False


COMISIONES: dict[str, ComisionPlataforma] = {
    "paypal": ComisionPlataforma(
        nombre="PayPal",
        porcentaje=0.0349,
        fijo_usd=0.49,
        spread_fx=0.025,
        descripcion="Pagos internacionales vía PayPal Business",
        fuente="paypal.com/co/webapps/mpp/merchant-fees",
        notas=[
            "Retiro a banco colombiano tiene cargo adicional ~$1 USD",
            "Spread 2.5% sobre tasa mid-market en conversión USD→COP",
            "Tarifa: 3.49% + $0.49 USD por transacción",
        ],
    ),
    "wise": ComisionPlataforma(
        nombre="Wise (TransferWise)",
        porcentaje=0.0041,
        fijo_usd=0.0,
        spread_fx=0.003,
        descripcion="Transferencia internacional con tasa mid-market",
        fuente="wise.com/co/pricing/",
        notas=[
            "Usa el tipo de cambio interbancario — opción más económica del mercado",
            "Tarifa real varía entre 0.35% y 0.6% según el banco receptor",
            "Recibo en cuenta colombiana en 1-2 días hábiles",
        ],
    ),
    "payoneer": ComisionPlataforma(
        nombre="Payoneer",
        porcentaje=0.02,
        fijo_usd=0.0,
        spread_fx=0.02,
        descripcion="Plataforma de pagos para freelancers y marketplaces",
        fuente="payoneer.com/es/support/fees/",
        notas=[
            "0% si el pago viene de otra cuenta Payoneer (wallet-to-wallet)",
            "2% cuando el cliente paga desde su empresa o banco",
            "Spread ~2% en conversión vs TRM oficial",
        ],
    ),
    "upwork": ComisionPlataforma(
        nombre="Upwork",
        porcentaje=0.10,
        fijo_usd=0.0,
        spread_fx=0.0,
        descripcion="Plataforma freelance (comisión escalonada por historial)",
        fuente="support.upwork.com/hc/en-us/articles/211062538",
        notas=[
            "20% primeros $500 con ese cliente, 10% de $500 a $10k, 5% arriba de $10k",
            "La comisión aplica sobre el valor bruto del contrato",
            "Usa tipo_upwork='nuevo'/'medio'/'senior' para calcular correctamente",
        ],
    ),
    "freelancer": ComisionPlataforma(
        nombre="Freelancer.com",
        fijo_es_minimo=True,
        porcentaje=0.10,
        fijo_usd=5.0,
        spread_fx=0.0,
        descripcion="Plataforma freelance con comisión 10% o mínimo $5 USD",
        fuente="freelancer.com/feeschedule.php",
        notas=[
            "Comisión: 10% del proyecto o $5 USD, lo que sea mayor",
            "Aplica igual para proyectos por hora y precio fijo",
            "Membresía Premium puede reducir comisiones",
        ],
    ),
    "binance": ComisionPlataforma(
        nombre="Binance P2P",
        porcentaje=0.001,
        fijo_usd=0.0,
        spread_fx=0.01,
        descripcion="Recibo en cripto vía Binance, conversión P2P a COP",
        fuente="binance.com/en/fee/schedule",
        notas=[
            "0.1% comisión trading spot (recibo de cripto)",
            "Spread P2P en COP: promedio 0.5-1.5% sobre precio de mercado",
            "Costo de red: USDT TRC20 ~$1, ERC20 ~$5-15 USD adicionales",
            "Mayor riesgo cambiario si cripto fluctúa durante transacción",
        ],
    ),
    "buda": ComisionPlataforma(
        nombre="Buda.com",
        porcentaje=0.008,
        fijo_usd=0.0,
        spread_fx=0.005,
        descripcion="Exchange colombiano de criptomonedas (regulado)",
        fuente="buda.com/fees",
        notas=[
            "Exchange de cripto con sede en Colombia",
            "Comisión maker/taker: 0.4-1.0% según volumen mensual",
            "Depósito y retiro COP sin costo adicional",
        ],
    ),
    "swift": ComisionPlataforma(
        nombre="SWIFT / Wire Transfer",
        porcentaje=0.0,
        fijo_usd=25.0,
        spread_fx=0.03,
        descripcion="Transferencia bancaria internacional SWIFT",
        fuente="Tarifas estándar bancos internacionales 2025",
        notas=[
            "Cargo fijo banco EMISOR: $25-35 USD (varía por banco)",
            "Banco RECEPTOR puede cobrar $5-15 adicionales",
            "Spread conversión bancario: 2-4% sobre TRM oficial",
            "Recomendado para montos grandes (>$2.000 USD)",
        ],
    ),
    "nequi": ComisionPlataforma(
        nombre="Nequi Internacional",
        porcentaje=0.02,
        fijo_usd=0.0,
        spread_fx=0.015,
        descripcion="Piloto de pagos internacionales Nequi/Bancolombia",
        fuente="nequi.com.co (piloto 2024-2025)",
        notas=[
            "Producto en fase piloto — tarifas sujetas a cambio",
            "Disponible para usuarios seleccionados de Bancolombia",
            "Verificar disponibilidad antes de usarlo con clientes",
        ],
    ),
}

UPWORK_TRAMOS = {
    "nuevo":  0.20,
    "medio":  0.10,
    "senior": 0.05,
}


def calcular_neto_plataforma(
    valor_usd: float,
    plataforma: str,
    trm: float,
    tipo_upwork: str = "nuevo",
    payoneer_tipo: str = "empresa",
) -> dict:
    """
    Calcula el neto en COP después de todas las comisiones de una plataforma.

    Args:
        valor_usd: Monto en USD que envía el cliente.
        plataforma: ID de la plataforma (paypal/wise/payoneer/upwork/freelancer/binance/buda/swift/nequi).
        trm: Tasa de cambio USD/COP (TRM oficial o del día).
        tipo_upwork: Para Upwork, tramo según historial ('nuevo'/'medio'/'senior').
        payoneer_tipo: Para Payoneer, 'wallet' (0%) o 'empresa' (2%).

    Returns:
        dict con: plataforma, valor_usd_bruto, comision_usd, valor_usd_neto,
                  trm_efectiva, valor_cop, costo_total_pct, notas.

    Examples:
        >>> r = calcular_neto_plataforma(1000, "wise", 4100)
        >>> r["valor_cop"] > 3_900_000
        True
    """
    if valor_usd <= 0:
        raise ValueError(f"El valor debe ser positivo: {valor_usd}")
    if plataforma not in COMISIONES:
        raise ValueError(f"Plataforma '{plataforma}' no existe. Opciones: {list(COMISIONES.keys())}")

    config = COMISIONES[plataforma]
    porcentaje = config.porcentaje

    if plataforma == "upwork":
        porcentaje = UPWORK_TRAMOS.get(tipo_upwork, 0.10)
    elif plataforma == "payoneer" and payoneer_tipo == "wallet":
        porcentaje = 0.0

    if config.fijo_es_minimo:
        comision_usd = max(valor_usd * porcentaje, config.fijo_usd)
    else:
        comision_usd = (valor_usd * porcentaje) + config.fijo_usd
    comision_usd = min(max(comision_usd, 0.0), valor_usd)
    valor_usd_neto = valor_usd - comision_usd

    trm_efectiva = trm * (1 - config.spread_fx)
    valor_cop = valor_usd_neto * trm_efectiva

    costo_comision_pct = comision_usd / valor_usd if valor_usd > 0 else 0
    costo_total_pct = round((costo_comision_pct + config.spread_fx) * 100, 2)

    return {
        "plataforma": config.nombre,
        "plataforma_id": plataforma,
        "valor_usd_bruto": valor_usd,
        "comision_pct": porcentaje,
        "comision_fijo_usd": config.fijo_usd,
        "comision_usd": round(comision_usd, 2),
        "valor_usd_neto": round(valor_usd_neto, 2),
        "spread_fx_pct": config.spread_fx,
        "trm_efectiva": round(trm_efectiva, 2),
        "valor_cop": round(valor_cop),
        "descripcion": config.descripcion,
        "notas": config.notas,
        "costo_total_pct": costo_total_pct,
        "tipo_upwork": tipo_upwork if plataforma == "upwork" else None,
    }


def listar_plataformas() -> list:
    """Retorna información básica de todas las plataformas disponibles."""
    return [
        {
            "id": pid,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "comision_base_pct": round(c.porcentaje * 100, 2),
            "fijo_usd": c.fijo_usd,
            "spread_fx_pct": round(c.spread_fx * 100, 2),
        }
        for pid, c in COMISIONES.items()
    ]
