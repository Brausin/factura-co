"""Pruebas de la página «Cuenta de cobro» de la app Streamlit.

Usa streamlit.testing.v1.AppTest para recorrer la página sin levantar un
servidor: navega por el menú lateral, envía el formulario y comprueba que
no se lanzan excepciones, que la validación responde y que se ofrece la
descarga del PDF.
"""

from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app" / "main.py")
PAGINA = "📄 Cuenta de cobro"


def _abrir_pagina():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.sidebar.radio[0].set_value(PAGINA).run()
    return at


def test_pagina_cuenta_cobro_carga_sin_excepciones():
    at = _abrir_pagina()
    assert not at.exception
    # El formulario expone su botón de envío.
    assert len(at.button) >= 1


def test_generar_cuenta_cobro_ofrece_descarga():
    at = _abrir_pagina()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.get("success")) == 1
    assert len(at.get("download_button")) == 1


def test_validacion_campo_obligatorio_bloquea_descarga():
    at = _abrir_pagina()
    at.text_input(key="cc_nombre").set_value("").run()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.get("error")) == 1
    assert len(at.get("download_button")) == 0


def test_aportes_se_muestran_al_activarlos():
    at = _abrir_pagina()
    # Toggle de aportes a seguridad social (informativo).
    at.toggle(key="cc_inc_ap").set_value(True).run()
    assert not at.exception
