"""Pruebas para el generador de facturas en PDF (factura_pdf)."""

from datetime import date

import pytest

from factura_co.factura_pdf import (
    generar_factura,
    guardar_factura,
    _desglose_factura,
    _normalizar_pct,
    _parse_fecha,
    _iniciales,
)


# Diccionario base válido reutilizable.
def _datos(**extra):
    base = {
        "nombre_freelancer": "Ana García",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": "Desarrollo de API de pagos — Sprint 3",
        "valor_cop": 5_000_000,
        "retencion_pct": 11,
    }
    base.update(extra)
    return base


# ── Desglose económico ───────────────────────────────────────────────────────

def test_desglose_calcula_retencion_y_total():
    d = _desglose_factura(_datos())
    assert d["subtotal"] == 5_000_000
    assert d["retencion_pct"] == pytest.approx(0.11)
    assert d["retencion_valor"] == 550_000
    assert d["total"] == 4_450_000


def test_desglose_sin_retencion():
    d = _desglose_factura(_datos(retencion_pct=0))
    assert d["retencion_valor"] == 0
    assert d["total"] == d["subtotal"] == 5_000_000


def test_desglose_acepta_fraccion_o_porcentaje():
    como_pct = _desglose_factura(_datos(retencion_pct=10))
    como_frac = _desglose_factura(_datos(retencion_pct=0.10))
    assert como_pct["retencion_valor"] == como_frac["retencion_valor"] == 500_000


def test_desglose_items_multiples_suman_subtotal():
    d = _desglose_factura(_datos(items=[("Diseño", 1_200_000),
                                        ("Implementación", 2_800_000)]))
    assert d["subtotal"] == 4_000_000
    assert len(d["items"]) == 2
    # retención 11% sobre el subtotal de los items
    assert d["retencion_valor"] == 440_000


def test_numero_factura_se_genera_si_falta():
    d = _desglose_factura(_datos(fecha="2026-06-07"))
    assert d["numero"] == "FV-20260607"


def test_numero_factura_respeta_el_provisto():
    d = _desglose_factura(_datos(numero_factura="FV-2026-014"))
    assert d["numero"] == "FV-2026-014"


# ── Validaciones ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("campo", [
    "nombre_freelancer", "nit_freelancer", "nombre_cliente",
    "nit_cliente", "descripcion_servicio", "valor_cop",
])
def test_falta_campo_obligatorio_lanza_error(campo):
    datos = _datos()
    del datos[campo]
    with pytest.raises(ValueError, match="obligatorios"):
        _desglose_factura(datos)


def test_campo_vacio_se_considera_faltante():
    with pytest.raises(ValueError, match="obligatorios"):
        _desglose_factura(_datos(nombre_cliente=""))


def test_valor_no_positivo_lanza_error():
    with pytest.raises(ValueError):
        _desglose_factura(_datos(valor_cop=0))
    with pytest.raises(ValueError):
        _desglose_factura(_datos(valor_cop=-100))


def test_valor_no_numerico_lanza_error():
    with pytest.raises(ValueError):
        _desglose_factura(_datos(valor_cop="cinco millones"))


def test_retencion_negativa_lanza_error():
    with pytest.raises(ValueError):
        _desglose_factura(_datos(retencion_pct=-5))


# ── Helpers ──────────────────────────────────────────────────────────────────

def test_normalizar_pct():
    assert _normalizar_pct(11) == pytest.approx(0.11)
    assert _normalizar_pct(0.11) == pytest.approx(0.11)
    assert _normalizar_pct(1) == pytest.approx(1.0)  # 100% como fracción
    assert _normalizar_pct(0) == 0.0


def test_parse_fecha_formatos():
    assert _parse_fecha(None) == date.today()
    assert _parse_fecha("2026-06-07") == date(2026, 6, 7)
    assert _parse_fecha("07/06/2026") == date(2026, 6, 7)
    assert _parse_fecha(date(2025, 1, 1)) == date(2025, 1, 1)


def test_iniciales():
    assert _iniciales("Ana García") == "AG"
    assert _iniciales("Carlos") == "CA"
    assert _iniciales("") == "FC"


# ── Generación del PDF ───────────────────────────────────────────────────────

def test_generar_factura_devuelve_pdf_valido():
    pdf = generar_factura(_datos())
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000  # un PDF real pesa varios KB


def test_generar_factura_con_todos_los_opcionales():
    pdf = generar_factura(_datos(
        fecha="2026-06-07",
        numero_factura="FV-2026-099",
        ciudad="Medellín",
        email="ana@ejemplo.co",
        telefono="300 123 4567",
        banco="Bancolombia",
        cuenta="123-456789-00",
        tipo_cuenta="Ahorros",
        notas="Pago a 15 días. Precios no incluyen IVA.",
    ))
    assert pdf[:4] == b"%PDF"


def test_generar_factura_falla_sin_obligatorio():
    datos = _datos()
    del datos["nit_cliente"]
    with pytest.raises(ValueError):
        generar_factura(datos)


def test_guardar_factura(tmp_path):
    pdf = generar_factura(_datos())
    ruta = tmp_path / "factura_test.pdf"
    resultado = guardar_factura(pdf, str(ruta))
    assert resultado == str(ruta)
    assert ruta.exists()
    assert ruta.read_bytes()[:4] == b"%PDF"


def test_descripcion_larga_no_rompe_generacion():
    desc = "Servicio integral de " + "consultoría y acompañamiento " * 20
    pdf = generar_factura(_datos(descripcion_servicio=desc))
    assert pdf[:4] == b"%PDF"
