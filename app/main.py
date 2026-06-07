"""
main.py -- Calculadora visual de ingresos para independientes colombianos.

Ejecutar:
    streamlit run app/main.py

Requiere:
    pip install streamlit pandas
"""

import sys
import json
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import pandas as pd

from factura_co.calculadora import calcular_neto
from factura_co.retenciones import (
    TABLA_RETENCIONES,
    calcular_ica,
    obtener_uvt,
    UVT_HISTORY,
)
from factura_co.aportes import SMMLV_2024, calcular_aportes
from factura_co.documento import generar_documento_txt
from factura_co import __version__

# Constantes
UVT_ACTUAL = obtener_uvt()

TIPOS_SERVICIO = {
    "honorarios":    "Honorarios -- consultoria, diseno, programacion (Art. 392)",
    "servicios":     "Servicios generales -- mantenimiento, instalacion (Art. 392)",
    "arrendamiento": "Arrendamiento de bien mueble o inmueble (Art. 401)",
    "compras":       "Compras de bienes o productos (Art. 401)",
    "transporte":    "Transporte nacional de carga o pasajeros (Art. 401)",
}

MUNICIPIOS_ICA = {
    "bogota":       "Bogota D.C.",
    "medellin":     "Medellin",
    "cali":         "Cali",
    "barranquilla": "Barranquilla",
    "otro":         "Otro municipio",
}

# Configuracion de pagina
st.set_page_config(
    page_title="factura-co | Calculadora freelancer Colombia",
    page_icon="CO",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.neto-valor { font-size: 2.8rem; font-weight: 900; color: #27ae60; letter-spacing:-1px; }
.neto-label { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.info-box { background: #f0f4ff; border-left: 4px solid #3498db; padding: 12px 16px; border-radius:4px; margin:8px 0; }
.warn-box { background: #fff8e1; border-left: 4px solid #f39c12; padding: 12px 16px; border-radius:4px; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("factura-co")
    st.caption(f"v{__version__} | Calculadora para independientes colombianos")
    st.divider()

    st.subheader("Tu factura")

    valor_factura = st.number_input(
        "Valor bruto (COP $)",
        min_value=1_000,
        max_value=1_000_000_000,
        value=5_000_000,
        step=100_000,
        format="%d",
        help="El valor que aparece en tu cuenta de cobro, antes de descuentos.",
    )

    tipo_servicio = st.selectbox(
        "Tipo de servicio",
        options=list(TIPOS_SERVICIO.keys()),
        format_func=lambda k: TIPOS_SERVICIO[k],
        help="Determina la tarifa de retencion aplicable segun el E.T.",
    )

    es_declarante = st.toggle(
        "Soy declarante de renta",
        value=False,
        help=(
            f"Activa si tus ingresos anuales superan ~${1_400 * UVT_ACTUAL / 1_000_000:.0f}M "
            f"(1.400 UVT x ${UVT_ACTUAL:,})."
        ),
    )

    incluir_aportes = st.toggle(
        "Incluir aportes a seguridad social",
        value=True,
        help="Salud (12.5%) y pension (16%) sobre el IBC (40% del ingreso)",
    )

    st.divider()
    st.subheader("ReteICA (opcional)")

    calcular_ica_flag = st.toggle(
        "Incluir ReteICA",
        value=False,
        help="Activa si tu cliente retiene ICA (Impuesto de Industria y Comercio)",
    )

    municipio_ica = "bogota"
    tipo_actividad_ica = "servicios_profesionales"

    if calcular_ica_flag:
        municipio_ica = st.selectbox(
            "Municipio",
            options=list(MUNICIPIOS_ICA.keys()),
            format_func=lambda k: MUNICIPIOS_ICA[k],
        )
        tipo_actividad_ica = st.selectbox(
            "Tipo de actividad",
            options=["servicios_profesionales", "servicios_generales", "comercio"],
            format_func=lambda x: {
                "servicios_profesionales": "Servicios profesionales",
                "servicios_generales": "Servicios generales",
                "comercio": "Comercio",
            }[x],
        )

    st.divider()
    st.caption(
        f"UVT {max(UVT_HISTORY.keys())}: ${UVT_ACTUAL:,} | "
        f"SMMLV 2024: ${SMMLV_2024:,}"
    )

# Calculo principal
try:
    resultado = calcular_neto(
        valor_factura=valor_factura,
        tipo_servicio=tipo_servicio,
        es_declarante=es_declarante,
        incluir_aportes=incluir_aportes,
    )
except ValueError as e:
    st.error(f"Error en el calculo: {e}")
    st.stop()

ret = resultado["retencion"]
aportes = resultado["aportes"]

ica_resultado = None
valor_ica = 0
if calcular_ica_flag:
    try:
        ica_resultado = calcular_ica(valor_factura, municipio_ica, tipo_actividad_ica)
        valor_ica = ica_resultado["valor_ica"]
    except Exception as e:
        st.sidebar.warning(f"Error ICA: {e}")

neto_final = resultado["neto"] - valor_ica

# Titulo
st.title("Calculadora de Ingresos para Independientes")
st.caption(
    "Retencion en la fuente * Aportes a seguridad social * "
    "Cuenta de cobro | Legislacion tributaria colombiana vigente"
)
st.divider()

# Dos columnas: retenciones | seguridad social
col_ret, col_ss = st.columns(2)

with col_ret:
    st.subheader("Retenciones")

    st.metric(
        label="Retencion en la fuente",
        value=f"${resultado['valor_retenido']:,.0f}",
        delta=f"{ret['tarifa_pct']} -- {ret['descripcion_tipo'][:45]}",
        delta_color="inverse",
    )
    st.caption(f"Referencia: {ret['articulo_et']} Estatuto Tributario")

    if ica_resultado:
        st.metric(
            label="ReteICA",
            value=f"${valor_ica:,.0f}",
            delta=f"{ica_resultado['tarifa_por_mil']}por mil -- {MUNICIPIOS_ICA[municipio_ica]}",
            delta_color="inverse",
        )
        st.caption(f"Fuente: {ica_resultado['descripcion_fuente']}")

    if not ret["aplica"]:
        st.markdown("""
        <div class="info-box">
        <strong>Sin retencion</strong>: el valor esta por debajo de la base minima
        exigida para este tipo de servicio.
        </div>
        """, unsafe_allow_html=True)

with col_ss:
    st.subheader("Seguridad Social")

    if incluir_aportes and aportes:
        st.metric(
            label="Aporte a salud",
            value=f"${aportes['aporte_salud']:,.0f}",
            delta=f"12.5% x IBC ${aportes['ibc']:,.0f}",
            delta_color="off",
        )
        st.metric(
            label="Aporte a pension",
            value=f"${aportes['aporte_pension']:,.0f}",
            delta=f"16% x IBC ${aportes['ibc']:,.0f}",
            delta_color="off",
        )
        ajuste = aportes["ibc_info"]["ajuste_aplicado"]
        st.caption(
            f"IBC = 40% del ingreso bruto. "
            f"{'Ajustado al minimo (1 SMMLV)' if ajuste == 'minimo' else 'IBC calculado sin ajuste'}"
        )
        if aportes["nota_minimo"]:
            st.markdown(f"""
            <div class="warn-box">
            {aportes['nota_minimo']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Los aportes no estan incluidos en este calculo.")

# NETO A RECIBIR
st.divider()
neto_pct = round(neto_final / valor_factura * 100, 1)

col_neto, col_detalles = st.columns([1, 2])

with col_neto:
    st.markdown('<p class="neto-label">NETO A RECIBIR</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="neto-valor">${neto_final:,.0f}</p>',
        unsafe_allow_html=True,
    )
    st.caption(f"El **{neto_pct}%** del valor bruto facturado")

with col_detalles:
    filas = [
        {"Concepto": "Valor bruto de la factura", "Monto (COP)": f"${valor_factura:,.0f}"},
        {"Concepto": f"- Retencion en la fuente ({ret['tarifa_pct']})", "Monto (COP)": f"-${resultado['valor_retenido']:,.0f}"},
    ]
    if ica_resultado:
        filas.append({
            "Concepto": f"- ReteICA ({ica_resultado['tarifa_por_mil']}por mil)",
            "Monto (COP)": f"-${valor_ica:,.0f}",
        })
    if incluir_aportes and aportes:
        filas.append({"Concepto": "- Aporte salud (12.5% x IBC)", "Monto (COP)": f"-${aportes['aporte_salud']:,.0f}"})
        filas.append({"Concepto": "- Aporte pension (16% x IBC)", "Monto (COP)": f"-${aportes['aporte_pension']:,.0f}"})
    filas.append({"Concepto": "NETO FINAL", "Monto (COP)": f"${neto_final:,.0f}"})

    df = pd.DataFrame(filas)
    st.dataframe(df, hide_index=True, use_container_width=True)

# Generar cuenta de cobro
st.divider()
st.subheader("Generar cuenta de cobro")

with st.expander("Completar datos del documento", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tus datos**")
        nombre = st.text_input("Nombre completo *", placeholder="Juan Vargas Ruiz")
        cedula = st.text_input("Cedula *", placeholder="79.123.456")
        ciudad_doc = st.text_input("Ciudad", value="Bogota", placeholder="Bogota")
        banco = st.text_input("Banco", placeholder="Bancolombia")
        cuenta_banco = st.text_input("Numero de cuenta", placeholder="123-456789-00")
        tipo_cta = st.selectbox("Tipo de cuenta", ["Ahorros", "Corriente"])

    with c2:
        st.markdown("**Datos del cliente**")
        empresa = st.text_input("Empresa / Razon social *", placeholder="Cliente S.A.S.")
        nit_cli = st.text_input("NIT del cliente *", placeholder="900.123.456-7")
        contacto = st.text_input("Nombre del contacto", placeholder="Maria Torres")
        descripcion_srv = st.text_area(
            "Descripcion del servicio *",
            placeholder="Consultoria en diseno de interfaz - Sprint 4",
            height=80,
        )
        numero_doc = st.text_input("Numero de documento", placeholder="DC-2024-001")

    generar_btn = st.button("Generar documento", type="primary")

    if generar_btn:
        faltantes = [f for f, v in [("Nombre", nombre), ("Cedula", cedula),
                     ("Empresa", empresa), ("NIT del cliente", nit_cli),
                     ("Descripcion", descripcion_srv)] if not v]
        if faltantes:
            st.warning(f"Completa los campos: {', '.join(faltantes)}")
        else:
            freelancer_data = {"nombre": nombre, "cedula": cedula, "ciudad": ciudad_doc or "Colombia"}
            if banco: freelancer_data["banco"] = banco
            if cuenta_banco:
                freelancer_data["cuenta"] = cuenta_banco
                freelancer_data["tipo_cuenta"] = tipo_cta

            cliente_data = {"empresa": empresa, "nit": nit_cli}
            if contacto: cliente_data["contacto"] = contacto

            txt_doc = generar_documento_txt(
                datos_freelancer=freelancer_data,
                datos_cliente=cliente_data,
                valor=valor_factura,
                descripcion=descripcion_srv,
                numero=numero_doc or None,
                incluir_retencion=True,
            )

            st.success("Documento generado")
            nombre_base = nombre.split()[0].lower()

            st.download_button(
                label="Descargar cuenta de cobro (.txt)",
                data=txt_doc.encode("utf-8"),
                file_name=f"cuenta_cobro_{nombre_base}.txt",
                mime="text/plain",
            )

            try:
                from factura_co.documento_pdf import generar_pdf
                pdf_bytes = generar_pdf(
                    datos_freelancer=freelancer_data,
                    datos_cliente=cliente_data,
                    valor=valor_factura,
                    descripcion=descripcion_srv,
                    numero=numero_doc or None,
                    incluir_retencion=True,
                    tarifa_retencion=ret["tarifa"],
                    incluir_ica=bool(ica_resultado),
                    valor_ica=valor_ica,
                    incluir_aportes=(incluir_aportes and bool(aportes)),
                    aporte_salud=aportes["aporte_salud"] if aportes else 0,
                    aporte_pension=aportes["aporte_pension"] if aportes else 0,
                )
                st.download_button(
                    label="Descargar cuenta de cobro (.pdf)",
                    data=pdf_bytes,
                    file_name=f"cuenta_cobro_{nombre_base}.pdf",
                    mime="application/pdf",
                )
            except Exception:
                pass

# Seccion educativa
st.divider()

with st.expander("Que es la retencion en la fuente?"):
    st.markdown(f"""
### Retencion en la fuente para freelancers colombianos

La **retencion en la fuente** es un mecanismo mediante el cual el pagador (tu cliente)
descuenta anticipadamente un porcentaje del valor que te paga y lo consigna a la DIAN.
Es un **anticipo del impuesto de renta**, no un impuesto adicional.

**Tarifas mas comunes para freelancers:**

| Tipo de servicio | No declarante | Declarante | Base minima |
|---|---|---|---|
| Honorarios (Art. 392) | **11%** | 10% | Sin minimo |
| Servicios (Art. 392) | **6%** | 4% | 4 UVT = ${4 * UVT_ACTUAL:,} |
| Arrendamiento (Art. 401) | **3.5%** | 3.5% | Sin minimo |

**Cuando soy declarante de renta?**
Si tus ingresos brutos anuales superan **1.400 UVT**
(aprox. ${1_400 * UVT_ACTUAL:,.0f} en {max(UVT_HISTORY.keys())}).

---
### Aportes a seguridad social (Ley 1607 de 2012)

- **Salud**: 12.5% del IBC
- **Pension**: 16% del IBC
- **IBC** = 40% del ingreso bruto (minimo 1 SMMLV = ${SMMLV_2024:,})

*Esta calculadora es orientativa. Para decisiones fiscales, consulta un contador certificado.*
""")

with st.expander("Historial del valor UVT (2015-2025)"):
    uvt_tabla = [
        {"Ano": str(a), "Valor UVT ($)": f"${v:,}", "Resolucion DIAN": "Ver uvt_history.json"}
        for a, v in sorted(UVT_HISTORY.items())
    ]
    st.dataframe(pd.DataFrame(uvt_tabla), hide_index=True)
    st.caption("Fuente: Resoluciones DIAN anuales. Art. 868 Estatuto Tributario.")

st.divider()
st.caption(
    f"factura-co v{__version__} | "
    "E.T. colombiano, Ley 1607/2012, Decreto 1601/2022 | "
    "[Codigo fuente](https://github.com/Brausin/factura-co)"
)
