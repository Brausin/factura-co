"""Tests para el módulo de plataformas de pago."""
import pytest
from factura_co.plataformas import (
    calcular_neto_plataforma,
    listar_plataformas,
    COMISIONES,
    UPWORK_TRAMOS,
)


# ---------------------------------------------------------------------------
# Tests básicos: estructura y cobertura
# ---------------------------------------------------------------------------

def test_listar_plataformas_retorna_todas():
    plats = listar_plataformas()
    assert len(plats) == len(COMISIONES)
    assert all("id" in p and "nombre" in p for p in plats)


def test_todas_las_plataformas_calculan_sin_error():
    """Todas las plataformas deben procesar $1000 USD sin errores."""
    for pid in COMISIONES:
        r = calcular_neto_plataforma(1000, pid, 4200)
        assert r["valor_cop"] > 0, f"Plataforma {pid} retornó COP <= 0"
        assert r["valor_usd_neto"] > 0, f"Plataforma {pid}: USD neto <= 0"
        assert "notas" in r and isinstance(r["notas"], list)


def test_plataforma_inexistente_lanza_error():
    with pytest.raises(ValueError, match="no existe"):
        calcular_neto_plataforma(1000, "bitcoin_magico", 4200)


def test_valor_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_neto_plataforma(-500, "wise", 4200)


def test_valor_cero_lanza_error():
    with pytest.raises(ValueError):
        calcular_neto_plataforma(0, "wise", 4200)


# ---------------------------------------------------------------------------
# Tests de valores concretos
# ---------------------------------------------------------------------------

def test_wise_es_la_mas_barata_en_comisiones():
    """Wise debe tener menor costo total que PayPal para montos medianos."""
    r_wise = calcular_neto_plataforma(1000, "wise", 4200)
    r_paypal = calcular_neto_plataforma(1000, "paypal", 4200)
    assert r_wise["valor_cop"] > r_paypal["valor_cop"]


def test_paypal_descuenta_cargo_fijo():
    r = calcular_neto_plataforma(1000, "paypal", 4200)
    # Comisión esperada: 1000 * 0.0349 + 0.49 = 35.39 USD
    assert abs(r["comision_usd"] - 35.39) < 0.10


def test_paypal_spread_fx_aplicado():
    r = calcular_neto_plataforma(1000, "paypal", 4200)
    # TRM efectiva = 4200 * (1 - 0.025) = 4095
    assert abs(r["trm_efectiva"] - 4095) < 1


def test_swift_cargo_fijo_domina_en_montos_bajos():
    """SWIFT con $25 fijos es proporcionalmente muy costoso en $100."""
    r = calcular_neto_plataforma(100, "swift", 4200)
    # Comisión = $25 fijos = 25% del valor
    assert r["comision_usd"] == 25.0
    assert r["valor_usd_neto"] == 75.0


def test_swift_cargo_fijo_insignificante_en_montos_altos():
    """SWIFT con $25 fijos es <1.25% en $2000."""
    r = calcular_neto_plataforma(2000, "swift", 4200)
    assert r["comision_usd"] == 25.0  # solo el fijo
    porcentaje_real = (r["comision_usd"] / 2000) * 100
    assert porcentaje_real < 2.0


# ---------------------------------------------------------------------------
# Tests de Upwork (escalonado)
# ---------------------------------------------------------------------------

def test_upwork_nuevo_paga_20_porciento():
    r = calcular_neto_plataforma(1000, "upwork", 4200, tipo_upwork="nuevo")
    assert r["comision_pct"] == 0.20
    assert abs(r["comision_usd"] - 200.0) < 0.01


def test_upwork_medio_paga_10_porciento():
    r = calcular_neto_plataforma(1000, "upwork", 4200, tipo_upwork="medio")
    assert r["comision_pct"] == 0.10
    assert abs(r["comision_usd"] - 100.0) < 0.01


def test_upwork_senior_paga_5_porciento():
    r = calcular_neto_plataforma(1000, "upwork", 4200, tipo_upwork="senior")
    assert r["comision_pct"] == 0.05
    assert abs(r["comision_usd"] - 50.0) < 0.01


def test_upwork_senior_mejor_que_nuevo():
    r_nuevo = calcular_neto_plataforma(1000, "upwork", 4200, tipo_upwork="nuevo")
    r_senior = calcular_neto_plataforma(1000, "upwork", 4200, tipo_upwork="senior")
    assert r_senior["valor_cop"] > r_nuevo["valor_cop"]


# ---------------------------------------------------------------------------
# Tests de Payoneer
# ---------------------------------------------------------------------------

def test_payoneer_empresa_cobra_2_porciento():
    r = calcular_neto_plataforma(1000, "payoneer", 4200, payoneer_tipo="empresa")
    assert r["comision_pct"] == 0.02


def test_payoneer_wallet_to_wallet_gratis():
    r = calcular_neto_plataforma(1000, "payoneer", 4200, payoneer_tipo="wallet")
    assert r["comision_pct"] == 0.0
    assert r["comision_usd"] == 0.0


def test_payoneer_wallet_mayor_que_empresa():
    r_wallet = calcular_neto_plataforma(1000, "payoneer", 4200, payoneer_tipo="wallet")
    r_empresa = calcular_neto_plataforma(1000, "payoneer", 4200, payoneer_tipo="empresa")
    assert r_wallet["valor_cop"] > r_empresa["valor_cop"]


# ---------------------------------------------------------------------------
# Tests de freelancer (cargo fijo dominante en montos bajos)
# ---------------------------------------------------------------------------

def test_freelancer_minimo_5usd():
    """Para $10 USD, cobra $5 mínimo (> 10% = $1)."""
    r = calcular_neto_plataforma(10, "freelancer", 4200)
    assert r["comision_usd"] == 5.0  # mínimo $5 aplica


def test_freelancer_10pct_domina_en_montos_altos():
    """Para $500 USD, 10% = $50 > $5 mínimo."""
    r = calcular_neto_plataforma(500, "freelancer", 4200)
    # max(500 * 0.10=50, 5) = 50
    assert abs(r["comision_usd"] - 50.0) < 0.01


# ---------------------------------------------------------------------------
# Tests de estructura de retorno
# ---------------------------------------------------------------------------

def test_resultado_tiene_todos_los_campos():
    r = calcular_neto_plataforma(1000, "wise", 4200)
    campos = [
        "plataforma", "plataforma_id", "valor_usd_bruto", "comision_pct",
        "comision_fijo_usd", "comision_usd", "valor_usd_neto", "spread_fx_pct",
        "trm_efectiva", "valor_cop", "descripcion", "notas", "costo_total_pct",
    ]
    for campo in campos:
        assert campo in r, f"Falta campo: {campo}"


def test_neto_cop_es_consistente():
    """valor_cop debe ser consistente con valor_usd_neto * trm_efectiva."""
    r = calcular_neto_plataforma(1000, "wise", 4200)
    esperado = r["valor_usd_neto"] * r["trm_efectiva"]
    assert abs(r["valor_cop"] - esperado) <= 1  # diferencia de redondeo


def test_costo_total_pct_mayor_que_comision():
    """costo_total_pct debe incluir spread FX además de comisión."""
    r = calcular_neto_plataforma(1000, "paypal", 4200)
    comision_solo_pct = (r["comision_usd"] / 1000) * 100
    assert r["costo_total_pct"] > comision_solo_pct  # incluye spread


def test_trm_afecta_cop_proporcionalmente():
    r1 = calcular_neto_plataforma(1000, "wise", 4000)
    r2 = calcular_neto_plataforma(1000, "wise", 5000)
    ratio = r2["valor_cop"] / r1["valor_cop"]
    assert abs(ratio - (5000 / 4000)) < 0.01
