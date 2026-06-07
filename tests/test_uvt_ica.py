"""
test_uvt_ica.py — Tests para historial de UVT, calcular_ica y documento_pdf.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.retenciones import (
    obtener_uvt,
    calcular_ica,
    UVT_HISTORY,
    UVT_2024,
    calcular_retencion,
)
from src.factura_co.documento_pdf import generar_pdf


# ── Tests UVT ─────────────────────────────────────────────────────────────────

class TestUVTHistory:
    def test_uvt_2024_valor_correcto(self):
        assert obtener_uvt(2024) == 47_065

    def test_uvt_2025_valor_correcto(self):
        assert obtener_uvt(2025) == 49_799

    def test_uvt_sin_año_retorna_vigente(self):
        """Sin parámetro retorna el UVT del año más reciente."""
        uvt = obtener_uvt()
        assert uvt == UVT_HISTORY[max(UVT_HISTORY.keys())]

    def test_uvt_2024_retrocompatible(self):
        """UVT_2024 sigue siendo 47.065 para retrocompatibilidad."""
        assert UVT_2024 == 47_065

    def test_historial_cubre_2015_a_2025(self):
        for año in range(2015, 2026):
            assert año in UVT_HISTORY, f"Falta UVT para {año}"

    def test_uvt_año_invalido(self):
        with pytest.raises(ValueError, match="no disponible"):
            obtener_uvt(1990)

    def test_uvt_incremental(self):
        """El UVT debe crecer año a año (no puede bajar)."""
        años = sorted(UVT_HISTORY.keys())
        for i in range(1, len(años)):
            assert UVT_HISTORY[años[i]] >= UVT_HISTORY[años[i - 1]]

    def test_retencion_usa_uvt_por_año(self):
        """calcular_retencion con año=2023 usa el UVT de 2023."""
        r = calcular_retencion(500_000, "servicios", año=2023)
        assert r["uvt_usado"] == obtener_uvt(2023)


# ── Tests ICA ─────────────────────────────────────────────────────────────────

class TestCalcularICA:
    def test_bogota_servicios_profesionales(self):
        """Bogotá: 9.66‰ para servicios profesionales."""
        ica = calcular_ica(3_000_000, "bogota", "servicios_profesionales")
        assert ica["tarifa_por_mil"] == 9.66
        assert ica["valor_ica"] == round(3_000_000 * 9.66 / 1000)

    def test_bogota_servicios_generales(self):
        ica = calcular_ica(2_000_000, "bogota", "servicios_generales")
        assert ica["tarifa_por_mil"] == 4.14
        assert ica["valor_ica"] == round(2_000_000 * 4.14 / 1000)

    def test_medellin_servicios_profesionales(self):
        ica = calcular_ica(5_000_000, "medellin", "servicios_profesionales")
        assert ica["tarifa_por_mil"] == 10.0
        assert ica["valor_ica"] == 50_000

    def test_tarifa_personalizada(self):
        """Se puede pasar una tarifa por mil personalizada."""
        ica = calcular_ica(1_000_000, "otro", tarifa_por_mil_personalizada=7.5)
        assert ica["tarifa_por_mil"] == 7.5
        assert ica["valor_ica"] == 7_500

    def test_valor_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="negativo"):
            calcular_ica(-100_000)

    def test_municipio_invalido_lanza_error(self):
        with pytest.raises(ValueError, match="no disponible"):
            calcular_ica(1_000_000, "cartagena")

    def test_neto_es_bruto_menos_ica(self):
        ica = calcular_ica(4_000_000, "cali", "servicios_profesionales")
        assert ica["valor_neto"] == 4_000_000 - ica["valor_ica"]

    def test_retorna_descripcion_fuente(self):
        ica = calcular_ica(1_000_000, "bogota")
        assert "Bogot" in ica["descripcion_fuente"]


# ── Tests PDF ─────────────────────────────────────────────────────────────────

class TestDocumentoPDF:
    @pytest.fixture
    def freelancer(self):
        return {
            "nombre": "Test Freelancer",
            "cedula": "12.345.678",
            "ciudad": "Bogota",
            "banco": "Bancolombia",
            "cuenta": "000-123456-00",
        }

    @pytest.fixture
    def cliente(self):
        return {
            "empresa": "Empresa Test S.A.S.",
            "nit": "900.000.001-1",
            "contacto": "Contacto Test",
        }

    def test_genera_pdf_valido(self, freelancer, cliente):
        pdf = generar_pdf(freelancer, cliente, 3_000_000, "Servicio de prueba")
        assert pdf[:4] == b"%PDF"

    def test_pdf_tiene_contenido(self, freelancer, cliente):
        pdf = generar_pdf(freelancer, cliente, 5_000_000, "Consultoria")
        assert len(pdf) > 1_000   # PDF real, no vacío

    def test_falta_campo_freelancer(self, cliente):
        with pytest.raises(ValueError, match="nombre"):
            generar_pdf({"cedula": "123"}, cliente, 1_000_000, "Test")

    def test_falta_campo_cliente(self, freelancer):
        with pytest.raises(ValueError, match="empresa"):
            generar_pdf(freelancer, {"nit": "900"}, 1_000_000, "Test")

    def test_pdf_con_retencion_e_ica(self, freelancer, cliente):
        pdf = generar_pdf(
            freelancer, cliente, 4_000_000, "Servicio con ICA",
            incluir_retencion=True, tarifa_retencion=0.11,
            incluir_ica=True, valor_ica=38_640,
        )
        assert pdf[:4] == b"%PDF"

    def test_pdf_con_aportes(self, freelancer, cliente):
        pdf = generar_pdf(
            freelancer, cliente, 8_000_000, "Servicio con aportes",
            incluir_aportes=True,
            aporte_salud=400_000,
            aporte_pension=512_000,
        )
        assert pdf[:4] == b"%PDF"

    def test_pdf_sin_datos_bancarios(self, cliente):
        """PDF funciona sin datos bancarios (opcionales)."""
        freelancer_min = {"nombre": "Minimo Test", "cedula": "99.999.999"}
        pdf = generar_pdf(freelancer_min, cliente, 2_000_000, "Minimo")
        assert pdf[:4] == b"%PDF"
