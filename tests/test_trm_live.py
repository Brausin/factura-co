"""Tests para el módulo trm_live de factura-co."""
import pytest
from factura_co.trm_live import get_trm_hoy, get_trm_info, _TRM_FALLBACK


def test_get_trm_retorna_float():
    trm = get_trm_hoy()
    assert isinstance(trm, float)


def test_get_trm_en_rango_razonable():
    trm = get_trm_hoy()
    assert 2_000 < trm < 8_000, f"TRM fuera de rango: {trm}"


def test_fallback_en_rango_razonable():
    assert 2_000 < _TRM_FALLBACK < 8_000


def test_get_trm_info_estructura():
    info = get_trm_info()
    assert "trm" in info
    assert "fecha_consulta" in info
    assert "fuente" in info
    assert "es_estimado" in info


def test_get_trm_info_trm_es_float():
    info = get_trm_info()
    assert isinstance(info["trm"], float)
    assert 2_000 < info["trm"] < 8_000


def test_get_trm_info_fecha_formato_iso():
    import re
    info = get_trm_info()
    assert re.match(r"\d{4}-\d{2}-\d{2}", info["fecha_consulta"])


def test_get_trm_verbose_no_lanza_error(capsys):
    get_trm_hoy(verbose=True)
    captured = capsys.readouterr()
    assert "TRM" in captured.out or len(captured.out) == 0  # puede estar vacío si falla red
