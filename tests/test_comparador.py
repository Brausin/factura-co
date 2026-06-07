"""Tests para el módulo comparador de plataformas."""
import pytest
from factura_co.comparador import (
    comparar_plataformas,
    tabla_comparacion,
    mejor_plataforma,
    peor_plataforma,
)
from factura_co.plataformas import COMISIONES


def test_comparar_retorna_todas_las_plataformas():
    resultados = comparar_plataformas(1000, 4200)
    assert len(resultados) == len(COMISIONES)


def test_comparar_ordenado_de_mayor_a_menor_cop():
    resultados = comparar_plataformas(1000, 4200)
    cops = [r["valor_cop"] for r in resultados]
    assert cops == sorted(cops, reverse=True)


def test_posiciones_asignadas_correctamente():
    resultados = comparar_plataformas(1000, 4200)
    for i, r in enumerate(resultados, 1):
        assert r["posicion"] == i


def test_mejor_plataforma_retorna_la_primera():
    mejor = mejor_plataforma(1000, 4200)
    todos = comparar_plataformas(1000, 4200)
    assert mejor["valor_cop"] == todos[0]["valor_cop"]


def test_peor_plataforma_retorna_la_ultima():
    peor = peor_plataforma(1000, 4200)
    todos = comparar_plataformas(1000, 4200)
    assert peor["valor_cop"] == todos[-1]["valor_cop"]


def test_tabla_es_string_no_vacio():
    tabla = tabla_comparacion(1000, 4200)
    assert isinstance(tabla, str)
    assert len(tabla) > 100


def test_tabla_contiene_plataformas_principales():
    tabla = tabla_comparacion(1000, 4200)
    assert "Wise" in tabla
    assert "PayPal" in tabla
    assert "SWIFT" in tabla


def test_tabla_top_n_limita_resultados():
    tabla_3 = tabla_comparacion(1000, 4200, top_n=3)
    tabla_completa = tabla_comparacion(1000, 4200)
    assert len(tabla_3) < len(tabla_completa)


def test_wise_generalmente_primera_para_montos_medianos():
    """Wise debería ser primera o segunda para $500-$2000 USD."""
    mejor = mejor_plataforma(1000, 4200)
    # Wise es casi siempre la mejor por su bajo spread
    todos = comparar_plataformas(1000, 4200)
    posicion_wise = next(r["posicion"] for r in todos if r["plataforma_id"] == "wise")
    assert posicion_wise <= 3  # al menos top 3


def test_swift_peor_para_montos_pequenos():
    """SWIFT con $25 fijos es muy costoso en $100."""
    todos = comparar_plataformas(100, 4200)
    posicion_swift = next(r["posicion"] for r in todos if r["plataforma_id"] == "swift")
    assert posicion_swift >= len(COMISIONES) - 2  # últimos 2


def test_upwork_nuevo_peor_que_senior():
    res_nuevo = comparar_plataformas(1000, 4200, tipo_upwork="nuevo")
    res_senior = comparar_plataformas(1000, 4200, tipo_upwork="senior")
    cop_nuevo = next(r["valor_cop"] for r in res_nuevo if r["plataforma_id"] == "upwork")
    cop_senior = next(r["valor_cop"] for r in res_senior if r["plataforma_id"] == "upwork")
    assert cop_senior > cop_nuevo


def test_diferencia_entre_mejor_y_peor_es_significativa():
    """Debe haber al menos 5% de diferencia entre mejor y peor."""
    mejor = mejor_plataforma(1000, 4200)
    peor = peor_plataforma(1000, 4200)
    diff_pct = (mejor["valor_cop"] - peor["valor_cop"]) / mejor["valor_cop"] * 100
    assert diff_pct > 5.0
