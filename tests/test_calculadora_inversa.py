"""Tests para calcular_bruto_necesario (calculadora inversa extendida)."""
import pytest
from factura_co.calculadora import calcular_bruto_necesario


def test_bruto_mayor_que_neto():
    r = calcular_bruto_necesario(3_000_000)
    assert r["bruto_necesario"] > 3_000_000


def test_neto_real_aproximado_al_deseado():
    """El neto real debe estar dentro de $1000 COP del deseado."""
    r = calcular_bruto_necesario(3_000_000, tolerancia=100)
    assert abs(r["neto_real"] - 3_000_000) < 1000


def test_diferentes_servicios():
    r_hon = calcular_bruto_necesario(3_000_000, "honorarios")
    r_ser = calcular_bruto_necesario(3_000_000, "servicios")
    # Honorarios tienen mayor retención, necesitan mayor bruto
    assert r_hon["bruto_necesario"] > r_ser["bruto_necesario"]


def test_sin_aportes_bruto_menor():
    r_con = calcular_bruto_necesario(3_000_000, incluir_aportes=True)
    r_sin = calcular_bruto_necesario(3_000_000, incluir_aportes=False)
    assert r_con["bruto_necesario"] > r_sin["bruto_necesario"]


def test_con_plataforma_retorna_usd():
    r = calcular_bruto_necesario(3_000_000, plataforma="wise", trm=4200)
    assert r["tiene_plataforma"] is True
    assert "bruto_usd_necesario" in r
    assert r["bruto_usd_necesario"] > 0


def test_con_plataforma_usd_razonable():
    """Para recibir 3M COP via Wise @ 4200, deberíamos necesitar ~714 USD."""
    r = calcular_bruto_necesario(3_000_000, plataforma="wise", trm=4200)
    # 3M COP neto after taxes needs ~900 USD bruto
    assert 850 < r["bruto_usd_necesario"] < 1050


def test_error_neto_negativo():
    with pytest.raises(ValueError):
        calcular_bruto_necesario(-100)


def test_estructura_resultado():
    r = calcular_bruto_necesario(3_000_000)
    assert "neto_deseado" in r
    assert "bruto_necesario" in r
    assert "neto_real" in r
    assert "diferencia" in r
    assert "desglose" in r
