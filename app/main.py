"""
main.py — Calculadora visual de ingresos para independientes colombianos.

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
from factura_co.plataformas import calcular_neto_plataforma, listar_plataformas
from factura_co.comparador import comparar_plataformas, tabla_comparacion
from factura_co.calculadora import calcular_bruto_necesario
from factura_co.trm_live import get_trm_info
from factura_co.proyeccion import proyeccion_anual, proyeccion_desde_usd, resumen_proyeccion

UVT_ACTUAL = obtener_uvt()
ANO_ACTUAL = max(UVT_HISTORY.keys())

TIPOS_SERVICIO = {
    "honorarios": {
        "label": "Honorarios",
        "descripcion": "Para consultores, abogados, medicos, disenadores, desarrolladores y otros profesionales independientes.",
        "icono": "💼",
        "articulo": "Art. 392 E.T.",
        "tarifa_nd": "11%",
        "tarifa_d": "10%",
    },
    "servicios": {
        "label": "Servicios generales",
        "descripcion": "Mantenimiento, instalacion, reparaciones y servicios tecnicos. Tarifa mas baja que honorarios.",
        "icono": "🔧",
        "articulo": "Art. 392 E.T.",
        "tarifa_nd": "6%",
        "tarifa_d": "4%",
    },
    "arrendamiento": {
        "label": "Arrendamiento",
        "descripcion": "Arriendo de inmuebles o bienes muebles. Tarifa fija independiente de si declara renta.",
        "icono": "🏠",
        "articulo": "Art. 401 E.T.",
        "tarifa_nd": "3.5%",
        "tarifa_d": "3.5%",
    },
    "compras": {
        "label": "Compras de bienes",
        "descripcion": "Venta de productos, materiales o bienes tangibles a empresas.",
        "icono": "📦",
        "articulo": "Art. 401 E.T.",
        "tarifa_nd": "2.5%",
        "tarifa_d": "2.5%",
    },
    "transporte": {
        "label": "Transporte",
        "descripcion": "Transporte nacional de carga o pasajeros.",
        "icono": "🚚",
        "articulo": "Art. 401 E.T.",
        "tarifa_nd": "3.5%",
        "tarifa_d": "3.5%",
    },
}

MUNICIPIOS_ICA = {
    "bogota": "Bogota D.C.",
    "medellin": "Medellin",
    "cali": "Cali",
    "barranquilla": "Barranquilla",
    "otro": "Otro municipio",
}

st.set_page_config(
    page_title="factura-co | Calculadora freelancer Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.neto-label { font-size: 0.85rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.1rem; }
.neto-valor { font-size: 2.8rem; font-weight: 800; color: #16a34a; margin: 0; }
.neto-pct   { font-size: 1rem; color: #6b7280; margin-top: 0.2rem; }
.caso-card {
    background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6;
    border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}
.caso-card h4 { margin: 0 0 0.3rem 0; color: #1e293b; font-size: 1rem; }
.caso-card p  { margin: 0; color: #475569; font-size: 0.875rem; }
.neto-card {
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border: 2px solid #16a34a; border-radius: 12px; padding: 1.5rem; text-align: center;
}
.warn-box {
    background: #fffbeb; border: 1px solid #f59e0b; border-radius: 6px;
    padding: 0.7rem 1rem; font-size: 0.85rem; color: #92400e;
}
</style>
""", unsafe_allow_html=True)


# SIDEBAR
with st.sidebar:
    st.markdown("## 🧾 factura-co")
    st.caption(f"v{__version__} · UVT {ANO_ACTUAL}: **${UVT_ACTUAL:,}**")
    st.divider()
    pagina = st.radio(
        "Ir a",
        ["🏠 Inicio", "🧮 Calculadora", "🔄 Cuanto cobrar?", "💱 Plataformas de pago", "📈 Proyeccion anual", "💡 Casos de uso", "📚 Aprende"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "Basado en el Estatuto Tributario colombiano.\n"
        "Esta herramienta es orientativa. Para decisiones fiscales, consulta un contador certificado."
    )


# INICIO
if pagina == "🏠 Inicio":
    st.markdown("# 🧾 factura-co")
    st.markdown("### Sabe cuanto te van a descontar de tu proxima factura?")
    st.markdown("""
Como freelancer o independiente en Colombia, cuando facturas $5.000.000 **no recibes $5.000.000**.

Tu cliente descuenta retencion en la fuente, tu pagas salud y pension, y al final te queda mucho menos de lo esperado.
**factura-co** te muestra exactamente cuanto, por que, y como planearlo.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
<div class="caso-card">
<h4>🔍 Calcula tu neto real</h4>
<p>Ingresa el valor de tu factura y ve al instante cuanto te queda despues de retenciones y aportes.</p>
</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="caso-card">
<h4>💰 Calcula cuanto cobrar</h4>
<p>Quieres recibir $4.000.000 netos? Calcula el valor bruto que debes facturar para llegar a eso.</p>
</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
<div class="caso-card">
<h4>📚 Entiende los numeros</h4>
<p>Aprende que es la retencion en la fuente, el IBC, el SMMLV y por que te descuentan lo que te descuentan.</p>
</div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### Que pasa con una factura de $5.000.000 en honorarios?")

    ejemplo = calcular_neto(5_000_000, "honorarios", es_declarante=False)
    apo_ej = ejemplo["aportes"]

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown(f"""
| Concepto | Monto |
|---|---|
| Valor bruto facturado | **$5.000.000** |
| Retencion en la fuente (11%) | -${ejemplo['valor_retenido']:,.0f} |
| IBC — base cotizacion (40%) | ${apo_ej['ibc']:,.0f} |
| Aporte salud (12.5% del IBC) | -${apo_ej['aporte_salud']:,.0f} |
| Aporte pension (16% del IBC) | -${apo_ej['aporte_pension']:,.0f} |
| **Ingreso neto real** | **${ejemplo['neto']:,.0f}** |
        """)
    with col_b:
        pct = round(ejemplo['neto'] / 5_000_000 * 100, 1)
        st.markdown(f"""
<div class="neto-card">
<p class="neto-label">De $5.000.000 te queda</p>
<p class="neto-valor">${ejemplo['neto']:,.0f}</p>
<p class="neto-pct">El <strong>{pct}%</strong> del valor facturado</p>
</div>
        """, unsafe_allow_html=True)

    st.divider()
    st.info("👈 Usa el menu lateral para ir a la Calculadora o ver los Casos de uso.")


# CALCULADORA PRINCIPAL
elif pagina == "🧮 Calculadora":
    st.markdown("## 🧮 Calculadora de ingresos")

    col_form, col_result = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("### Parametros de la factura")

        tipo_key = st.selectbox(
            "Tipo de servicio",
            options=list(TIPOS_SERVICIO.keys()),
            format_func=lambda k: f"{TIPOS_SERVICIO[k]['icono']} {TIPOS_SERVICIO[k]['label']}",
        )
        info_tipo = TIPOS_SERVICIO[tipo_key]
        st.caption(f"📖 {info_tipo['descripcion']} · *{info_tipo['articulo']}*")
        st.caption(f"Tarifa: **{info_tipo['tarifa_nd']}** (no declarante) / **{info_tipo['tarifa_d']}** (declarante)")

        valor_factura = st.number_input(
            "Valor bruto de la factura (COP)",
            min_value=0,
            max_value=500_000_000,
            value=5_000_000,
            step=100_000,
            format="%d",
        )

        es_declarante = st.toggle(
            "Soy declarante de renta",
            value=False,
            help=f"Eres declarante si tus ingresos anuales superan 1.400 UVT aprox. ${1_400 * UVT_ACTUAL:,.0f} en {ANO_ACTUAL}.",
        )

        incluir_aportes = st.toggle(
            "Incluir aportes a seguridad social",
            value=True,
            help="Salud (12.5%) y pension (16%) calculados sobre el 40% del ingreso bruto (IBC).",
        )

        with st.expander("🏙️ Agregar ReteICA (opcional)"):
            incluir_ica = st.checkbox("Incluir ReteICA en el calculo", value=False)
            municipio_sel = st.selectbox(
                "Municipio",
                options=list(MUNICIPIOS_ICA.keys()),
                format_func=lambda k: MUNICIPIOS_ICA[k],
                disabled=not incluir_ica,
            )
            actividad_sel = st.selectbox(
                "Tipo de actividad",
                ["servicios_profesionales", "servicios_generales", "comercio", "industria"],
                disabled=not incluir_ica,
            )

    with col_result:
        st.markdown("### Resultado")

        if valor_factura == 0:
            st.info("Ingresa el valor de tu factura para ver el calculo.")
        else:
            resultado = calcular_neto(
                valor_factura,
                tipo_key,
                es_declarante=es_declarante,
                incluir_aportes=incluir_aportes,
            )

            ret = resultado["retencion"]
            aportes = resultado["aportes"]
            valor_retenido = resultado["valor_retenido"]

            ica_resultado = None
            valor_ica = 0
            if incluir_ica:
                try:
                    ica_resultado = calcular_ica(valor_factura, municipio_sel, actividad_sel)
                    valor_ica = ica_resultado["valor_ica"]
                except Exception:
                    pass

            neto_final = resultado["neto"] - valor_ica
            neto_pct = round(neto_final / valor_factura * 100, 1)

            base_min_uvt = ret.get("base_minima_uvt", 0)
            umbral_pesos = base_min_uvt * UVT_ACTUAL
            if umbral_pesos > 0 and valor_factura < umbral_pesos:
                st.warning(
                    f"El valor facturado (${valor_factura:,.0f}) es menor al umbral minimo para retencion "
                    f"({base_min_uvt} UVT = ${umbral_pesos:,.0f}). No aplica retencion en la fuente."
                )

            st.markdown(f"""
<div class="neto-card">
<p class="neto-label">Neto a recibir</p>
<p class="neto-valor">${neto_final:,.0f}</p>
<p class="neto-pct">El <strong>{neto_pct}%</strong> de tu factura</p>
</div>
            """, unsafe_allow_html=True)
            st.markdown("")

            filas = [
                ("💵 Valor bruto facturado", f"${valor_factura:,.0f}", ""),
                (f"🏛️ Retencion en la fuente ({ret['tarifa_pct']})", f"-${valor_retenido:,.0f}", "Tu cliente lo paga a la DIAN"),
            ]
            if ica_resultado:
                filas.append((f"🏙️ ReteICA ({ica_resultado['tarifa_por_mil']}‰)", f"-${valor_ica:,.0f}", f"ICA {MUNICIPIOS_ICA.get(municipio_sel, municipio_sel)}"))
            if incluir_aportes and aportes:
                filas.append((f"🏥 Salud (12.5% x IBC ${aportes['ibc']:,.0f})", f"-${aportes['aporte_salud']:,.0f}", "Cotizacion como independiente"))
                filas.append((f"🏦 Pension (16% x IBC)", f"-${aportes['aporte_pension']:,.0f}", "Cotizacion como independiente"))
            filas.append(("✅ Neto final", f"${neto_final:,.0f}", ""))

            df = pd.DataFrame(filas, columns=["Concepto", "Monto (COP)", "Nota"])
            st.dataframe(df, hide_index=True, use_container_width=True)

            with st.expander("❓ Por que me descuentan retencion en la fuente?"):
                st.markdown(f"""
La retencion en la fuente es un **anticipo del impuesto de renta**. Tu cliente lo recauda y lo
entrega a la DIAN en tu nombre. **No es un impuesto adicional** — cuando declares renta, ese valor
genera un saldo a favor o reduce lo que debes pagar.

- Tarifa aplicada: **{ret['tarifa_pct']}** ({'declarante' if es_declarante else 'no declarante de renta'})
- Base legal: {info_tipo['articulo']}
                """)

            if incluir_aportes and aportes:
                with st.expander("❓ Como se calculan los aportes a salud y pension?"):
                    st.markdown(f"""
Como independiente pagas salud y pension **por tu cuenta**:

- **IBC** = 40% del ingreso bruto = ${aportes['ibc']:,.0f}
- **Salud**: 12.5% del IBC = ${aportes['aporte_salud']:,.0f}
- **Pension**: 16% del IBC = ${aportes['aporte_pension']:,.0f}
- **IBC minimo**: 1 SMMLV = ${SMMLV_2024:,}

Base legal: Art. 18 Ley 100/1993, Decreto 1601/2022.
                    """)

    # Cuenta de cobro
    st.divider()
    st.markdown("### 📄 Generar cuenta de cobro")

    with st.expander("Completar datos del documento", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Tus datos**")
            nombre = st.text_input("Nombre completo *", placeholder="Laura Gomez Rios")
            cedula = st.text_input("Cedula *", placeholder="52.123.456")
            ciudad_doc = st.text_input("Ciudad", value="Bogota")
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
                placeholder="Consultoria en diseno de interfaz — Sprint 4",
                height=80,
            )
            numero_doc = st.text_input("Numero de documento", placeholder="CC-2025-001")

        if st.button("Generar documento", type="primary"):
            faltantes = [f for f, v in [("Nombre", nombre), ("Cedula", cedula), ("Empresa", empresa), ("NIT", nit_cli), ("Descripcion", descripcion_srv)] if not v]
            if faltantes:
                st.warning(f"Completa los campos: {', '.join(faltantes)}")
            else:
                v_calc = valor_factura if valor_factura else 0
                freelancer_data = {"nombre": nombre, "cedula": cedula, "ciudad": ciudad_doc or "Colombia"}
                if banco: freelancer_data["banco"] = banco
                if cuenta_banco:
                    freelancer_data["cuenta"] = cuenta_banco
                    freelancer_data["tipo_cuenta"] = tipo_cta
                cliente_data = {"empresa": empresa, "nit": nit_cli}
                if contacto: cliente_data["contacto"] = contacto
                txt_doc = generar_documento_txt(
                    datos_freelancer=freelancer_data, datos_cliente=cliente_data,
                    valor=v_calc, descripcion=descripcion_srv, numero=numero_doc or None, incluir_retencion=True,
                )
                st.success("Documento generado")
                nombre_base = nombre.split()[0].lower() if nombre else "freelancer"
                st.download_button("⬇️ Descargar (.txt)", txt_doc.encode("utf-8"), f"cuenta_cobro_{nombre_base}.txt", "text/plain")
                try:
                    from factura_co.documento_pdf import generar_pdf
                    ret_calc = calcular_neto(v_calc, tipo_key, es_declarante, incluir_aportes)
                    r = ret_calc["retencion"]; a = ret_calc["aportes"] or {}
                    pdf_bytes = generar_pdf(
                        datos_freelancer=freelancer_data, datos_cliente=cliente_data,
                        valor=v_calc, descripcion=descripcion_srv, numero=numero_doc or None,
                        incluir_retencion=True, tarifa_retencion=r["tarifa"],
                        incluir_ica=bool(ica_resultado), valor_ica=valor_ica,
                        incluir_aportes=(incluir_aportes and bool(a)),
                        aporte_salud=a.get("aporte_salud", 0), aporte_pension=a.get("aporte_pension", 0),
                    )
                    st.download_button("⬇️ Descargar (.pdf)", pdf_bytes, f"cuenta_cobro_{nombre_base}.pdf", "application/pdf")
                except Exception:
                    pass


# CALCULADORA INVERSA
elif pagina == "🔄 Cuanto cobrar?":
    st.markdown("## 🔄 Cuanto debo cobrar para recibir lo que necesito?")
    st.markdown("Ingresa cuanto quieres recibir **neto** y la calculadora te dice cuanto debes facturar en **bruto**.")

    col_inv, col_inv_r = st.columns([1, 1], gap="large")

    with col_inv:
        neto_deseado = st.number_input(
            "Cuanto quieres recibir? (COP neto)",
            min_value=0, max_value=200_000_000, value=4_000_000, step=100_000, format="%d",
        )
        tipo_inv = st.selectbox(
            "Tipo de servicio",
            options=list(TIPOS_SERVICIO.keys()),
            format_func=lambda k: f"{TIPOS_SERVICIO[k]['icono']} {TIPOS_SERVICIO[k]['label']}",
            key="inv_tipo",
        )
        declarante_inv = st.toggle("Soy declarante de renta", key="inv_declarante")
        aportes_inv = st.toggle("Incluir aportes a seguridad social", value=True, key="inv_aportes")
        st.info("Esta calculadora usa busqueda iterativa para encontrar el bruto exacto.")

    with col_inv_r:
        if neto_deseado > 0:
            # Busqueda iterativa
            bruto_est = float(neto_deseado)
            for _ in range(60):
                r_temp = calcular_neto(bruto_est, tipo_inv, declarante_inv, aportes_inv)
                diferencia = neto_deseado - r_temp["neto"]
                if abs(diferencia) < 500:
                    break
                bruto_est += diferencia * 1.2

            bruto_final = round(bruto_est / 1000) * 1000
            resultado_inv = calcular_neto(bruto_final, tipo_inv, declarante_inv, aportes_inv)
            neto_obtenido = resultado_inv["neto"]
            ret_inv = resultado_inv["retencion"]
            apo_inv = resultado_inv["aportes"]

            st.markdown(f"""
<div class="neto-card">
<p class="neto-label">Debes facturar (bruto)</p>
<p class="neto-valor">${bruto_final:,.0f}</p>
<p class="neto-pct">Para recibir aprox. <strong>${neto_obtenido:,.0f}</strong> neto</p>
</div>
            """, unsafe_allow_html=True)
            st.markdown("")

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.metric("Bruto a facturar", f"${bruto_final:,.0f}")
                st.metric("Retencion", f"-${resultado_inv['valor_retenido']:,.0f}", delta=f"-{ret_inv['tarifa_pct']}", delta_color="inverse")
            with col_r2:
                if aportes_inv and apo_inv:
                    st.metric("Aportes SS", f"-${apo_inv['aporte_salud'] + apo_inv['aporte_pension']:,.0f}", delta_color="inverse")
                st.metric("Neto estimado", f"${neto_obtenido:,.0f}")

            filas_inv = [
                ("💵 Valor a facturar (bruto)", f"${bruto_final:,.0f}"),
                (f"🏛️ Retencion ({ret_inv['tarifa_pct']})", f"-${resultado_inv['valor_retenido']:,.0f}"),
            ]
            if aportes_inv and apo_inv:
                filas_inv.append(("🏥 Salud (12.5% IBC)", f"-${apo_inv['aporte_salud']:,.0f}"))
                filas_inv.append(("🏦 Pension (16% IBC)", f"-${apo_inv['aporte_pension']:,.0f}"))
            filas_inv.append(("✅ Neto estimado", f"${neto_obtenido:,.0f}"))
            st.dataframe(pd.DataFrame(filas_inv, columns=["Concepto", "Monto"]), hide_index=True, use_container_width=True)
        else:
            st.info("Ingresa el neto que quieres recibir.")


# CASOS DE USO
elif pagina == "💡 Casos de uso":
    st.markdown("## 💡 Casos de uso reales")
    st.markdown("Escenarios concretos para que puedas comparar con tu situacion.")

    CASOS = [
        {
            "titulo": "Desarrollador web — Honorarios $5.000.000",
            "emoji": "💻",
            "descripcion": "Juan es desarrollador freelance. Su cliente empresa le paga $5.000.000 por el desarrollo de un modulo. Juan no es declarante de renta.",
            "valor": 5_000_000,
            "tipo": "honorarios",
            "declarante": False,
            "aportes": True,
            "contexto": "El caso mas comun para profesionales tech independientes. La tarifa del 11% aplica sobre el total.",
        },
        {
            "titulo": "Disenadora — Servicios $1.800.000 (debajo del umbral)",
            "emoji": "🎨",
            "descripcion": "Laura es disenadora grafica. Factura $1.800.000 por servicios de diseno. Quiere saber si aplica retencion.",
            "valor": 1_800_000,
            "tipo": "servicios",
            "declarante": False,
            "aportes": True,
            "contexto": "Para 'servicios' aplica un umbral minimo de 4 UVT. Verifica si este valor supera el umbral.",
        },
        {
            "titulo": "Abogado — Honorarios $15.000.000 (declarante)",
            "emoji": "⚖️",
            "descripcion": "Carlos es abogado con ingresos anuales que superan $70 millones. Factura $15.000.000 por honorarios. Es declarante de renta.",
            "valor": 15_000_000,
            "tipo": "honorarios",
            "declarante": True,
            "aportes": True,
            "contexto": "Al ser declarante, la tarifa baja de 11% a 10%. En altos valores, esta diferencia es significativa.",
        },
        {
            "titulo": "Consultor — $8.000.000 con ReteICA Bogota",
            "emoji": "📊",
            "descripcion": "Valentina es consultora de negocios en Bogota. Factura $8.000.000 a una empresa bogotana.",
            "valor": 8_000_000,
            "tipo": "honorarios",
            "declarante": False,
            "aportes": True,
            "contexto": "En Bogota los servicios profesionales tienen ReteICA de 9.66‰. Se suma al impacto total.",
            "ica": {"municipio": "bogota", "actividad": "servicios_profesionales"},
        },
    ]

    for caso in CASOS:
        with st.expander(f"{caso['emoji']} {caso['titulo']}", expanded=False):
            col_d, col_r = st.columns([1, 1])
            with col_d:
                st.markdown(f"**Situacion:** {caso['descripcion']}")
                st.markdown(f"*{caso['contexto']}*")
                st.markdown(f"- **Valor:** ${caso['valor']:,.0f}\n- **Tipo:** {TIPOS_SERVICIO[caso['tipo']]['label']}\n- **Declarante:** {'Si' if caso['declarante'] else 'No'}")

            with col_r:
                res = calcular_neto(caso["valor"], caso["tipo"], caso["declarante"], caso["aportes"])
                ret_c = res["retencion"]
                apo_c = res["aportes"]
                valor_ica_c = 0
                ica_c = None
                if "ica" in caso:
                    try:
                        ica_c = calcular_ica(caso["valor"], caso["ica"]["municipio"], caso["ica"]["actividad"])
                        valor_ica_c = ica_c["valor_ica"]
                    except Exception:
                        pass

                neto_c = res["neto"] - valor_ica_c
                pct_c = round(neto_c / caso["valor"] * 100, 1)

                umbral_uvt = ret_c.get("base_minima_uvt", 0)
                umbral_pesos = umbral_uvt * UVT_ACTUAL
                if umbral_pesos > 0 and caso["valor"] < umbral_pesos:
                    st.warning(f"El valor no supera el umbral minimo ({umbral_uvt} UVT = ${umbral_pesos:,.0f}). No aplica retencion.")

                st.metric("Bruto facturado", f"${caso['valor']:,.0f}")
                st.metric("Retencion en la fuente", f"-${res['valor_retenido']:,.0f}", delta=f"{ret_c['tarifa_pct']}", delta_color="inverse")
                if ica_c:
                    st.metric(f"ReteICA ({ica_c['tarifa_por_mil']}‰)", f"-${valor_ica_c:,.0f}", delta_color="inverse")
                if caso["aportes"] and apo_c:
                    st.metric("Aportes SS", f"-${apo_c['aporte_salud'] + apo_c['aporte_pension']:,.0f}", delta_color="inverse")
                st.markdown(f"""
<div class="neto-card">
<p class="neto-label">Neto a recibir</p>
<p class="neto-valor">${neto_c:,.0f}</p>
<p class="neto-pct">El <strong>{pct_c}%</strong> del valor facturado</p>
</div>
                """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Tu caso es diferente?")
    st.markdown("Usa la **Calculadora** en el menu lateral para ingresar tus propios numeros.")


# APRENDE
elif pagina == "📚 Aprende":
    st.markdown("## 📚 Aprende: retenciones para independientes colombianos")
    st.markdown("Todo lo que necesitas entender, explicado sin jerga tributaria innecesaria.")

    with st.expander("🏛️ Que es la retencion en la fuente y quien la paga?", expanded=True):
        st.markdown(f"""
**La retencion en la fuente** es un mecanismo de recaudo anticipado del impuesto de renta.
Cuando una empresa te paga, **descuenta un porcentaje y lo entrega a la DIAN en tu nombre**.

Es un **anticipo del impuesto de renta**, no un impuesto adicional. Cuando declares renta, ese
dinero ya retenido se descuenta de lo que debes pagar — o te lo devuelven si fue de mas.

**Cuando NO aplica:**
- Cuando el pagador es una persona natural sin obligacion de retener.
- Cuando el valor esta por debajo del umbral minimo (segun tipo de servicio).
- Cuando eres parte del regimen simple de tributacion.

### Tarifas vigentes {ANO_ACTUAL} (UVT = ${UVT_ACTUAL:,})

| Tipo de servicio | No declarante | Declarante | Umbral minimo |
|---|---|---|---|
| Honorarios (Art. 392) | **11%** | 10% | Sin umbral |
| Servicios (Art. 392) | **6%** | 4% | 4 UVT = ${4 * UVT_ACTUAL:,} |
| Arrendamiento (Art. 401) | **3.5%** | 3.5% | Sin umbral |
| Compras (Art. 401) | **2.5%** | 2.5% | 27 UVT = ${27 * UVT_ACTUAL:,} |
| Transporte (Art. 401) | **3.5%** | 3.5% | 4 UVT = ${4 * UVT_ACTUAL:,} |

*Fuente: Estatuto Tributario, Art. 392-401. Decreto 2231 de 2023.*
        """)

    with st.expander("🏥 IBC: que es y como se calcula?"):
        st.markdown(f"""
**IBC (Ingreso Base de Cotizacion)** es el valor sobre el que calculas y pagas salud y pension.

### La regla del 40%
Como independiente, tu IBC es el **40% de tu ingreso bruto**.
Si facturas $5.000.000, tu IBC es $2.000.000.

El 60% restante se considera costos y gastos de tu actividad.

### Cuanto pago?
| Concepto | Tarifa | Sobre el IBC (si facturas $5M) |
|---|---|---|
| Salud | 12.5% | ${int(0.125 * 0.4 * 5_000_000):,} |
| Pension | 16% | ${int(0.16 * 0.4 * 5_000_000):,} |
| **Total SS** | **28.5%** | **${int(0.285 * 0.4 * 5_000_000):,}** |

- Minimo: 1 SMMLV = **${SMMLV_2024:,}**
- Maximo: 25 SMMLV = ${25 * SMMLV_2024:,}

*Fuente: Art. 18 Ley 100/1993, Decreto 1601 de 2022.*
        """)

    with st.expander("💼 Diferencia entre honorarios, servicios y arrendamiento"):
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.markdown("**Honorarios**\n\nPrestacion de servicios basada en conocimiento profesional: consultoria, diseno, desarrollo, asesoria legal, medicina.\n\nTarifa alta: **11% / 10%**. Sin umbral minimo.")
        with col_t2:
            st.markdown(f"**Servicios**\n\nMantenimiento, instalacion, reparacion, limpieza. No requieren titulo profesional.\n\nTarifa media: **6% / 4%**. Umbral: 4 UVT = ${4 * UVT_ACTUAL:,}")
        with col_t3:
            st.markdown("**Arrendamiento**\n\nAlquiler de inmuebles o bienes muebles.\n\nTarifa fija: **3.5%** (igual para declarantes y no declarantes). Sin umbral minimo.")

    with st.expander("📋 Cuando soy declarante de renta?"):
        st.markdown(f"""
Eres obligado a declarar renta en {ANO_ACTUAL} si cumples alguna de estas condiciones:

1. Ingresos brutos >= 1.400 UVT aprox. **${1_400 * UVT_ACTUAL:,.0f}**
2. Patrimonio >= 4.500 UVT aprox. ${4_500 * UVT_ACTUAL:,.0f}
3. Compras con tarjeta >= 1.400 UVT
4. Consignaciones >= 1.400 UVT

**Vale la pena declarar si no estoy obligado?** Si te retuvieron dinero, si. Al declarar puedes pedir la devolucion del saldo a favor.

*Fuente: Art. 592-594 E.T.*
        """)

    with st.expander("📖 Glosario de terminos"):
        glosario = {
            "UVT": f"Unidad de Valor Tributario. Unidad de medida tributaria que se actualiza con la inflacion. En {ANO_ACTUAL} vale ${UVT_ACTUAL:,}. Fijada anualmente por la DIAN.",
            "SMMLV": f"Salario Minimo Mensual Legal Vigente. En 2024 fue ${SMMLV_2024:,}. Base minima para cotizacion a seguridad social.",
            "IBC": "Ingreso Base de Cotizacion. El valor sobre el que calculas salud y pension. Para independientes es el 40% del ingreso bruto.",
            "Retencion en la fuente": "Anticipo del impuesto de renta que tu cliente recauda y entrega a la DIAN por ti.",
            "Agente retenedor": "La empresa o persona que te paga y tiene la obligacion de descontar y pagar la retencion.",
            "DIAN": "Direccion de Impuestos y Aduanas Nacionales. Entidad que administra los impuestos nacionales en Colombia.",
            "ReteICA": "Retencion del Impuesto de Industria y Comercio. Lo cobra el municipio sobre actividades economicas en su territorio.",
            "E.T.": "Estatuto Tributario. Norma principal que regula los impuestos nacionales (Decreto 624 de 1989 y modificaciones).",
            "Declarante de renta": "Persona que supera los topes de ingresos o patrimonio y esta obligada a presentar declaracion de renta.",
        }
        for term, defn in glosario.items():
            st.markdown(f"**{term}**: {defn}")

    with st.expander(f"📈 Historial UVT 2015-{ANO_ACTUAL}"):
        uvt_tabla = [
            {"Ano": str(a), "Valor UVT ($)": f"${v:,}", "Var. desde 2015": f"+{round((v / 28279 - 1) * 100, 1)}%"}
            for a, v in sorted(UVT_HISTORY.items())
        ]
        st.dataframe(pd.DataFrame(uvt_tabla), hide_index=True)
        st.caption("Fuente: Resoluciones DIAN anuales. Art. 868 Estatuto Tributario.")

    st.divider()
    st.caption("Contenido orientativo. Para decisiones fiscales, consulta un contador publico certificado.")



# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA: PLATAFORMAS DE PAGO
# ──────────────────────────────────────────────────────────────────────────────
elif pagina == "💱 Plataformas de pago":
    st.markdown("# 💱 Plataformas de pago internacional")
    st.markdown("Compara cuánto recibes en COP según por dónde te pague el cliente.")

    # TRM
    trm_info = get_trm_info()
    trm_default = trm_info["trm"]
    fuente_trm = trm_info["fuente"]

    col_trm, col_monto = st.columns(2)
    with col_trm:
        trm = st.number_input(
            "TRM (COP por 1 USD)",
            min_value=1000.0, max_value=10000.0,
            value=float(round(trm_default)),
            step=10.0,
            help=f"Fuente: {fuente_trm}",
        )
    with col_monto:
        valor_usd = st.number_input(
            "Valor en USD que te pagan",
            min_value=1.0, max_value=100000.0,
            value=1000.0, step=50.0,
        )

    tipo_upwork = st.select_slider(
        "Historial en Upwork",
        options=["nuevo", "medio", "senior"],
        value="nuevo",
        help="nuevo: <$500 con ese cliente | medio: $500-$10k | senior: >$10k",
    )

    st.divider()

    # Tabla comparación
    resultados = comparar_plataformas(valor_usd, trm, tipo_upwork)
    mejor = resultados[0]
    peor = resultados[-1]

    col_m, col_p, col_d = st.columns(3)
    with col_m:
        st.metric("✅ Mejor opción", mejor["plataforma"],
                  f"${mejor['valor_cop']:,.0f} COP")
    with col_p:
        st.metric("❌ Peor opción", peor["plataforma"],
                  f"${peor['valor_cop']:,.0f} COP")
    with col_d:
        diff = mejor["valor_cop"] - peor["valor_cop"]
        st.metric("💰 Diferencia", f"${diff:,.0f} COP",
                  f"{(diff/mejor['valor_cop']*100):.1f}% más con la mejor")

    st.divider()

    # Tabla detallada
    tabla_data = []
    for r in resultados:
        tabla_data.append({
            "#": r["posicion"],
            "Plataforma": r["plataforma"],
            "USD que llegan": f"${r['valor_usd_neto']:,.2f}",
            "Comisión USD": f"-${r['comision_usd']:,.2f}",
            "TRM efectiva": f"${r['trm_efectiva']:,.0f}",
            "Recibes COP": f"${r['valor_cop']:,.0f}",
            "Costo total %": f"{r['costo_total_pct']:.1f}%",
        })

    df_tabla = pd.DataFrame(tabla_data)
    st.dataframe(df_tabla, hide_index=True, use_container_width=True)

    # Notas de la plataforma seleccionada
    nombres_plat = [r["plataforma"] for r in resultados]
    plat_sel_nombre = st.selectbox("Ver detalles de:", nombres_plat)
    plat_sel = next(r for r in resultados if r["plataforma"] == plat_sel_nombre)
    if plat_sel["notas"]:
        st.markdown("**Notas importantes:**")
        for nota in plat_sel["notas"]:
            st.markdown(f"- {nota}")

    st.caption("Comisiones aproximadas basadas en tarifas publicadas 2025. Verifica antes de usar.")


# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA: PROYECCIÓN ANUAL
# ──────────────────────────────────────────────────────────────────────────────
elif pagina == "📈 Proyeccion anual":
    st.markdown("# 📈 Proyección anual de ingresos")
    st.markdown("Cuánto queda realmente después de retenciones, aportes e impuesto de renta.")

    col1, col2 = st.columns(2)
    with col1:
        modo_moneda = st.radio("Moneda de ingreso", ["Pesos COP", "Dólares USD"])
    with col2:
        meses = st.slider("Meses a proyectar", 1, 12, 12)

    if modo_moneda == "Pesos COP":
        ingreso_mensual = st.number_input(
            "Ingreso mensual bruto (COP)",
            min_value=100_000, max_value=100_000_000,
            value=5_000_000, step=500_000,
            format="%d",
        )

        col_serv, col_dec = st.columns(2)
        with col_serv:
            tipo_str = st.selectbox(
                "Tipo de servicio",
                ["honorarios", "servicios", "arrendamiento", "compras"],
                index=0,
            )
        with col_dec:
            es_declarante = st.checkbox("Soy declarante de renta", value=True)

        proy = proyeccion_anual(
            ingreso_mensual, tipo_str, es_declarante, incluir_aportes=True, meses=meses
        )

    else:  # USD
        trm_info2 = get_trm_info()
        col_usd, col_trm2 = st.columns(2)
        with col_usd:
            ingreso_usd = st.number_input(
                "Ingreso mensual (USD)",
                min_value=100.0, max_value=100000.0,
                value=1000.0, step=100.0,
            )
        with col_trm2:
            trm2 = st.number_input(
                "TRM",
                min_value=1000.0, max_value=10000.0,
                value=float(round(trm_info2["trm"])),
                step=10.0,
            )

        plataformas_lista = listar_plataformas()
        plat_nombres = {p["nombre"]: p["id"] for p in plataformas_lista}
        plat_sel2 = st.selectbox("Plataforma de cobro", list(plat_nombres.keys()))
        plat_id2 = plat_nombres[plat_sel2]

        tipo_str = st.selectbox("Tipo de servicio", ["honorarios", "servicios"], index=0)
        es_declarante = st.checkbox("Soy declarante de renta", value=True)

        proy = proyeccion_desde_usd(
            ingreso_usd, trm2, plat_id2, tipo_str, es_declarante, meses
        )

    st.divider()

    # Métricas principales
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Bruto anual", f"${proy['ingreso_bruto_anual']:,.0f}")
    with col_b:
        st.metric("Neto disponible anual", f"${proy['neto_anual']:,.0f}",
                  f"{proy['neto_pct_bruto']:.1f}% del bruto")
    with col_c:
        st.metric("Promedio mensual real", f"${proy['neto_mensual_promedio']:,.0f}")

    # Desglose
    st.markdown("### Desglose de obligaciones")
    desglose_data = [
        {"Concepto": "Ingreso bruto anual", "Monto": f"${proy['ingreso_bruto_anual']:,.0f}", "Nota": ""},
        {"Concepto": "(-) Aportes seguridad social", "Monto": f"-${proy['total_aportes_anual']:,.0f}", "Nota": "Salud + pensión"},
        {"Concepto": "(-) Impuesto de renta estimado", "Monto": f"-${proy['impuesto_renta_estimado']:,.0f}", "Nota": f"Tasa efectiva: {proy['tasa_renta_efectiva_pct']:.1f}%"},
        {"Concepto": "= NETO DISPONIBLE", "Monto": f"${proy['neto_anual']:,.0f}", "Nota": f"{proy['neto_pct_bruto']:.1f}% del bruto"},
    ]
    st.dataframe(pd.DataFrame(desglose_data), hide_index=True, use_container_width=True)

    st.info(f"💡 **Ahorro mensual recomendado** para cubrir aportes y diferencia de renta: "
            f"**${proy['ahorro_mensual_recomendado']:,.0f} COP/mes**")

    st.caption("Estimado. Impuesto de renta simplificado (Art. 241 E.T.). "
               "Consulte un contador para su declaración real.")


# FOOTER
st.divider()
st.caption(
    f"factura-co v{__version__} · UVT {ANO_ACTUAL}: ${UVT_ACTUAL:,} · "
    "E.T. colombiano, Ley 1607/2012, Decreto 1601/2022 · "
    "[Codigo fuente](https://github.com/Brausin/factura-co)"
)
