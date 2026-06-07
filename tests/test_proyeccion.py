"""Tests para el módulo de proyección anual."""
import pytest
from factura_co.proyeccion import (
    proyeccion_anual,
    proyeccion_desde_usd,
    calcular_impuesto_renta,
    resumen_proyeccion,
)


# ---------------------------------------------------------------------------
# Tests de impuesto de renta
# ---------------------------------------------------------------------------

def test_impuesto_cero_bajo_umbral():
    """Renta menor a 1090 UVT no paga impuesto (1090 * 47065 = ~51.3M)."""
    # $40M COP < umbral 1090 UVT (51.3M)
    r = calcular_impuesto_renta(40_000_000)
    assert r["impuesto_cop"] == 0


def test_impuesto_positivo_sobre_umbral():
    r = calcular_impuesto_renta(100_000_000)
    assert r["impuesto_cop"] > 0


def test_impuesto_tasa_progresiva():
    """Mayor ingreso debe tener mayor tasa efectiva."""
    r1 = calcular_impuesto_renta(80_000_000)
    r2 = calcular_impuesto_renta(200_000_000)
    assert r2["tasa_efectiva_pct"] > r1["tasa_efectiva_pct"]


def test_impuesto_estructura():
    r = calcular_impuesto_renta(100_000_000)
    assert "renta_liquida_cop" in r
    assert "renta_uvt" in r
    assert "impuesto_cop" in r
    assert "tasa_efectiva_pct" in r


# ---------------------------------------------------------------------------
# Tests de proyección anual básica
# ---------------------------------------------------------------------------

def test_proyeccion_bruto_anual_correcto():
    r = proyeccion_anual(5_000_000)
    assert r["ingreso_bruto_anual"] == 60_000_000


def test_proyeccion_6_meses():
    r = proyeccion_anual(5_000_000, meses=6)
    assert r["ingreso_bruto_anual"] == 30_000_000
    assert r["meses_proyectados"] == 6


def test_neto_menor_que_bruto():
    r = proyeccion_anual(5_000_000)
    assert r["neto_anual"] < r["ingreso_bruto_anual"]


def test_neto_positivo():
    r = proyeccion_anual(5_000_000)
    assert r["neto_anual"] > 0


def test_aportes_reducen_neto():
    r_con = proyeccion_anual(5_000_000, incluir_aportes=True)
    r_sin = proyeccion_anual(5_000_000, incluir_aportes=False)
    assert r_con["neto_anual"] < r_sin["neto_anual"]


def test_neto_pct_en_rango_razonable():
    """El neto debe ser entre 40% y 90% del bruto para un freelancer colombiano."""
    r = proyeccion_anual(5_000_000)
    assert 40 < r["neto_pct_bruto"] < 90


def test_estructura_completa():
    r = proyeccion_anual(5_000_000)
    campos = [
        "ingreso_mensual_bruto", "ingreso_bruto_anual", "total_retenciones_anual",
        "total_aportes_anual", "renta_liquida_estimada", "impuesto_renta_estimado",
        "neto_anual", "neto_mensual_promedio", "neto_pct_bruto",
        "ahorro_mensual_recomendado",
    ]
    for campo in campos:
        assert campo in r, f"Falta campo: {campo}"


def test_ahorro_recomendado_positivo():
    r = proyeccion_anual(5_000_000)
    assert r["ahorro_mensual_recomendado"] >= 0


# ---------------------------------------------------------------------------
# Tests de proyección desde USD
# ---------------------------------------------------------------------------

def test_proyeccion_usd_retorna_dict():
    r = proyeccion_desde_usd(1000, 4200, "wise")
    assert isinstance(r, dict)


def test_proyeccion_usd_tiene_campos_extra():
    r = proyeccion_desde_usd(1000, 4200, "wise")
    assert "ingreso_mensual_usd" in r
    assert "trm_usada" in r
    assert "plataforma_cobro" in r


def test_proyeccion_usd_mayor_trm_mayor_neto():
    r1 = proyeccion_desde_usd(1000, 4000, "wise")
    r2 = proyeccion_desde_usd(1000, 5000, "wise")
    assert r2["neto_anual"] > r1["neto_anual"]


def test_proyeccion_usd_paypal_menor_que_wise():
    r_wise = proyeccion_desde_usd(1000, 4200, "wise")
    r_paypal = proyeccion_desde_usd(1000, 4200, "paypal")
    assert r_wise["neto_anual"] > r_paypal["neto_anual"]


# ---------------------------------------------------------------------------
# Tests de resumen
# ---------------------------------------------------------------------------

def test_resumen_es_string():
    r = proyeccion_anual(5_000_000)
    texto = resumen_proyeccion(r)
    assert isinstance(texto, str)
    assert len(texto) > 100


def test_resumen_contiene_datos_clave():
    r = proyeccion_anual(5_000_000)
    texto = resumen_proyeccion(r)
    assert "PROYECCIÓN" in texto
    assert "NETO" in texto
