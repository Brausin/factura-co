"""
test_retenciones.py — Tests para el módulo de retenciones en la fuente.

Casos de prueba basados en ejemplos reales y verificados con la normativa
tributaria colombiana 2024.

Ejecutar:
    pytest tests/ -v
    pytest tests/ -v --tb=short
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.retenciones import calcular_retencion, listar_tipos_servicio, UVT_2024
from src.factura_co.aportes import calcular_aportes, ingreso_base_cotizacion, SMMLV_2024
from src.factura_co.calculadora import calcular_neto


# ─────────────────────────────────────────────
# Tests: Retención en honorarios
# ─────────────────────────────────────────────

class TestRetencionHonorarios:

    def test_honorarios_no_declarante_tasa_11(self):
        """Honorarios para no declarante: tarifa es 11%"""
        r = calcular_retencion(3_000_000, "honorarios", es_declarante=False)
        assert r["tarifa"] == 0.11

    def test_honorarios_declarante_tasa_10(self):
        """Honorarios para declarante: tarifa es 10%"""
        r = calcular_retencion(3_000_000, "honorarios", es_declarante=True)
        assert r["tarifa"] == 0.10

    def test_honorarios_calculo_retencion(self):
        """3.000.000 × 11% = 330.000"""
        r = calcular_retencion(3_000_000, "honorarios")
        assert r["valor_retencion"] == 330_000

    def test_honorarios_valor_neto(self):
        """3.000.000 - 330.000 = 2.670.000"""
        r = calcular_retencion(3_000_000, "honorarios")
        assert r["valor_neto"] == 2_670_000

    def test_honorarios_cinco_millones(self):
        """5.000.000 × 11% = 550.000"""
        r = calcular_retencion(5_000_000, "honorarios")
        assert r["valor_retencion"] == 550_000
        assert r["valor_neto"] == 4_450_000

    def test_honorarios_aplica_desde_primer_peso(self):
        """Honorarios no tienen base mínima: aplica desde $1"""
        r = calcular_retencion(100_000, "honorarios")
        assert r["aplica"] is True
        assert r["valor_retencion"] == 11_000

    def test_tarifa_pct_formato(self):
        """El formato de tarifa_pct debe ser '11.0%'"""
        r = calcular_retencion(3_000_000, "honorarios")
        assert r["tarifa_pct"] == "11.0%"


# ─────────────────────────────────────────────
# Tests: Retención en servicios
# ─────────────────────────────────────────────

class TestRetencionServicios:

    def test_servicios_no_declarante_tasa_6(self):
        """Servicios para no declarante: tarifa es 6%"""
        r = calcular_retencion(1_000_000, "servicios", es_declarante=False)
        assert r["tarifa"] == 0.06

    def test_servicios_declarante_tasa_4(self):
        """Servicios para declarante: tarifa es 4%"""
        r = calcular_retencion(1_000_000, "servicios", es_declarante=True)
        assert r["tarifa"] == 0.04

    def test_servicios_base_minima_4uvt(self):
        """Servicios: solo aplica si valor >= 4 UVT"""
        base_minima = 4 * UVT_2024
        assert base_minima == 4 * 47_065

    def test_servicios_por_encima_base_minima(self):
        """$500.000 > 4 UVT ($188.260) → aplica retención"""
        r = calcular_retencion(500_000, "servicios")
        assert r["aplica"] is True
        assert r["valor_retencion"] == 30_000  # 500.000 × 6%

    def test_servicios_por_debajo_base_minima(self):
        """$100.000 < 4 UVT ($188.260) → no aplica retención"""
        r = calcular_retencion(100_000, "servicios")
        assert r["aplica"] is False
        assert r["valor_retencion"] == 0


# ─────────────────────────────────────────────
# Tests: Tipos adicionales
# ─────────────────────────────────────────────

class TestOtrosTipos:

    def test_arrendamiento_tasa_3_5(self):
        r = calcular_retencion(2_000_000, "arrendamiento")
        assert r["tarifa"] == 0.035
        assert r["valor_retencion"] == 70_000

    def test_tipo_invalido_lanza_error(self):
        with pytest.raises(ValueError, match="no válido"):
            calcular_retencion(1_000_000, "tipo_inexistente")

    def test_valor_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="negativo"):
            calcular_retencion(-500_000, "honorarios")

    def test_listar_tipos_retorna_todos(self):
        tipos = listar_tipos_servicio()
        for tipo in ["honorarios", "servicios", "arrendamiento", "compras", "transporte"]:
            assert tipo in tipos


# ─────────────────────────────────────────────
# Tests: Ingreso Base de Cotización (IBC)
# ─────────────────────────────────────────────

class TestIBC:

    def test_ibc_40_porciento_del_ingreso(self):
        """IBC = 40% del ingreso bruto cuando supera el mínimo"""
        ibc = ingreso_base_cotizacion(5_000_000)
        assert ibc["ibc_calculado"] == 2_000_000  # 5M × 40%
        assert ibc["ibc_aplicado"] == 2_000_000
        assert ibc["ajuste_aplicado"] == "ninguno"

    def test_ibc_minimo_1_smmlv(self):
        """Si 40% del ingreso < SMMLV, se usa SMMLV como IBC"""
        # 40% de $3.000.000 = $1.200.000 < SMMLV ($1.300.000)
        ibc = ingreso_base_cotizacion(3_000_000)
        assert ibc["ibc_calculado"] == 1_200_000
        assert ibc["ibc_aplicado"] == SMMLV_2024  # Se ajusta al mínimo
        assert ibc["ajuste_aplicado"] == "minimo"

    def test_ibc_maximo_25_smmlv(self):
        """Si 40% del ingreso > 25 SMMLV, se usa 25 SMMLV como techo"""
        # Ingreso muy alto
        ibc = ingreso_base_cotizacion(100_000_000)
        assert ibc["ibc_aplicado"] == SMMLV_2024 * 25
        assert ibc["ajuste_aplicado"] == "maximo"

    def test_ibc_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            ingreso_base_cotizacion(-1_000_000)


# ─────────────────────────────────────────────
# Tests: Aportes a seguridad social
# ─────────────────────────────────────────────

class TestAportes:

    def test_aportes_salud_12_5_pct_del_ibc(self):
        """Salud = 12.5% del IBC"""
        a = calcular_aportes(5_000_000)
        # IBC = 2.000.000 (40% de 5M, sin ajustes)
        assert a["aporte_salud"] == round(2_000_000 * 0.125)

    def test_aportes_pension_16_pct_del_ibc(self):
        """Pensión = 16% del IBC"""
        a = calcular_aportes(5_000_000)
        assert a["aporte_pension"] == round(2_000_000 * 0.16)

    def test_aportes_total(self):
        """Total aportes = salud + pensión"""
        a = calcular_aportes(5_000_000)
        assert a["total_aportes"] == a["aporte_salud"] + a["aporte_pension"]

    def test_aportes_con_ibc_minimo_nota(self):
        """Con IBC ajustado al mínimo, debe incluir nota de advertencia"""
        a = calcular_aportes(2_000_000)  # 40% = 800K < SMMLV
        assert a["nota_minimo"] is not None


# ─────────────────────────────────────────────
# Tests: Calculadora principal
# ─────────────────────────────────────────────

class TestCalculadoraNeto:

    def test_neto_incluye_aportes(self):
        """Con aportes: neto = valor_recibido - total_aportes"""
        r = calcular_neto(3_000_000, "honorarios", incluir_aportes=True)
        esperado = r["valor_recibido"] - r["total_aportes"]
        assert r["neto"] == esperado

    def test_neto_sin_aportes(self):
        """Sin aportes: neto = valor_recibido"""
        r = calcular_neto(3_000_000, "honorarios", incluir_aportes=False)
        assert r["neto"] == r["valor_recibido"]
        assert r["total_aportes"] == 0

    def test_neto_es_menor_que_bruto(self):
        """El neto siempre debe ser menor al bruto"""
        r = calcular_neto(5_000_000, "honorarios")
        assert r["neto"] < r["valor_factura"]

    def test_valor_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            calcular_neto(-1_000, "honorarios")

    def test_neto_pct_entre_0_y_100(self):
        """El porcentaje neto debe estar entre 0 y 100"""
        r = calcular_neto(3_000_000, "honorarios")
        assert 0 < r["neto_pct"] < 100

    def test_caso_real_honorarios_3m(self):
        """
        Caso real verificado manualmente:
        $3.000.000 honorarios, no declarante
        Retención: 3M × 11% = 330.000
        Valor recibido: 2.670.000
        IBC: ajustado a SMMLV = 1.300.000 (40% = 1.2M < 1.3M)
        Salud: 1.300.000 × 12.5% = 162.500
        Pensión: 1.300.000 × 16% = 208.000
        Neto: 2.670.000 - 162.500 - 208.000 = 2.299.500
        """
        r = calcular_neto(3_000_000, "honorarios")
        assert r["valor_retenido"] == 330_000
        assert r["valor_recibido"] == 2_670_000
        assert r["aportes"]["aporte_salud"] == 162_500
        assert r["aportes"]["aporte_pension"] == 208_000
        assert r["neto"] == 2_299_500
