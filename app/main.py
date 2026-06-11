"""
main.py — factura-co · Calculadora financiera para freelancers colombianos.

Aplicación Streamlit con estética "dark finance": navegación por secciones,
componentes visuales custom (ver app/ui.py) y gráficos Plotly. Reúne todas las
herramientas del paquete factura_co en una sola interfaz:

    Inicio · Plataformas · Comparador · Calculadora inversa · Proyección · Factura

Ejecutar:
    streamlit run app/main.py
"""

import sys
from pathlib import Path
from datetime import date

# Permite importar el paquete tanto instalado como desde ./src
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd

from factura_co import __version__
from factura_co.aportes import SMMLV_VIGENTE, calcular_aportes
from factura_co.calculadora import calcular_neto, calcular_bruto_necesario
from factura_co.plataformas import calcular_neto_plataforma, listar_plataformas
from factura_co.comparador import comparar_plataformas, mejor_plataforma
from factura_co.proyeccion import proyeccion_anual, proyeccion_desde_usd
from factura_co.trm_live import get_trm_info
from factura_co.factura_pdf import generar_factura, _desglose_factura
from factura_co.documento_pdf import generar_pdf as generar_cuenta_cobro

import ui
from ui import COLORS, card, fila_cards, barra_h, badge, seccion, md

C = COLORS  # alias corto para los f-strings de estilo


# ── Configuración base ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="factura-co · Finanzas freelancer Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.apply_styles()


TIPOS_SERVICIO = {
    "honorarios": "💼 Honorarios (consultoría, desarrollo, diseño)",
    "servicios": "🔧 Servicios generales (técnicos, mantenimiento)",
    "arrendamiento": "🏠 Arrendamiento",
    "compras": "📦 Compras de bienes",
    "transporte": "🚚 Transporte",
}

UPWORK_TRAMOS = {
    "nuevo": "Nuevo cliente (20% / 10%)",
    "medio": "Cliente recurrente",
    "senior": "Cliente consolidado (5%)",
}

PLATAFORMAS = listar_plataformas()
PLAT_NOMBRES = {p["id"]: p["nombre"] for p in PLATAFORMAS}


@st.cache_data(ttl=1800, show_spinner=False)
def trm_info_cached() -> dict:
    """TRM en vivo con caché de 30 min para no llamar la API en cada rerun."""
    return get_trm_info()


def trm_badge(info: dict) -> str:
    """Pill de estado de la TRM: ámbar si es estimada, verde si es oficial."""
    if info["es_estimado"]:
        return ("<span style='background:#7c4a00;color:#F5A623;"
                "border:1px solid #F5A623;border-radius:20px;padding:2px 10px;"
                "font-size:11px'>⚠️ Estimado</span>")
    return ("<span style='background:#003c2a;color:#00C896;"
            "border:1px solid #00C896;border-radius:20px;padding:2px 10px;"
            "font-size:11px'>✅ Oficial · datos.gov.co</span>")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · INICIO
# ─────────────────────────────────────────────────────────────────────────────
def pagina_inicio(trm_info: dict):
    trm = trm_info["trm"]
    md("<div style='font-size:34px;font-weight:700;letter-spacing:-.02em'>"
       "factura&#8209;co</div>"
       f"<div style='color:{C['muted']};font-size:15px;margin-bottom:6px'>"
       "Cuánto recibes realmente como freelancer en Colombia — retenciones, "
       "aportes, comisiones de plataforma y proyección anual.</div>")

    smmlv_usd = SMMLV_VIGENTE / trm
    mejor = mejor_plataforma(1000, trm)

    md(seccion("Indicadores de hoy", trm_info["fuente"]))
    md(fila_cards([
        card("TRM USD/COP", ui.fmt_cop(trm), trm_badge(trm_info), COLORS["blue"]),
        card("Mejor plataforma · US$1.000", mejor["plataforma"],
             f"Neto {ui.fmt_cop(mejor['valor_cop'])}", COLORS["green"]),
        card("SMMLV en dólares", ui.fmt_usd(smmlv_usd),
             f"{ui.fmt_cop(SMMLV_VIGENTE)} / mes (2026)", COLORS["gold"]),
    ]))

    md(f"<div style='background:{C['card']};border:1px solid {C['border']};"
       f"border-radius:12px;padding:14px 18px;margin:10px 0;font-size:15px;"
       f"display:flex;align-items:center;gap:10px;flex-wrap:wrap'>"
       f"<span>Con la TRM de hoy → <b>US$1.000 = {ui.fmt_cop(trm * 1000)}</b></span>"
       f"{trm_badge(trm_info)}</div>")

    # Top plataformas para una referencia de US$1.000
    comp = comparar_plataformas(1000, trm)
    md(seccion("Recibir US$1.000 hoy", "Neto en COP según plataforma de cobro"))
    fig = ui.plotly_barras_h(
        [r["plataforma"] for r in comp],
        [r["valor_cop"] for r in comp],
        color=COLORS["green"], fmt="$,.0f",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    md(seccion("Herramientas", ""))
    cols = st.columns(3)
    tarjetas = [
        ("💱 Plataformas", "Comisión real de PayPal, Wise, Payoneer, Upwork y más."),
        ("🔄 Comparador", "Cuál te deja más COP para un monto en USD."),
        ("🧮 Calculadora inversa", "Cuánto cobrar para recibir un neto objetivo."),
        ("📈 Proyección", "Renta anual estimada con Art. 241 ET."),
        ("🧾 Factura", "Genera un PDF profesional listo para enviar."),
        ("📊 Datos reales", "Comisiones y tarifas oficiales, TRM en vivo."),
    ]
    for i, (titulo, desc) in enumerate(tarjetas):
        with cols[i % 3]:
            md(f"<div style='background:{C['card']};border:1px solid {C['border']};"
               f"border-radius:12px;padding:16px;margin:6px 0;min-height:96px'>"
               f"<div style='font-weight:600;font-size:15px'>{titulo}</div>"
               f"<div style='color:{C['muted']};font-size:13px;margin-top:6px'>"
               f"{desc}</div></div>")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · PLATAFORMAS
# ─────────────────────────────────────────────────────────────────────────────
def pagina_plataformas(trm_info: dict):
    md("<div style='font-size:26px;font-weight:700'>💱 Plataformas de cobro</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>Comisión real y neto en "
       "pesos para un pago internacional.</div>")

    col1, col2 = st.columns([1, 1])
    with col1:
        valor_usd = st.slider("Monto del cliente (USD)", 50, 10_000, 1_000, 50)
    with col2:
        plat_id = st.selectbox("Plataforma", [p["id"] for p in PLATAFORMAS],
                               format_func=lambda x: PLAT_NOMBRES[x])

    trm_def = min(max(int(round(trm_info["trm"])), 3_000), 6_500)
    trm = float(st.slider("Simular TRM (escenario USD/COP)", 3_000, 6_500,
                          trm_def, 50,
                          help="Mueve la TRM para ver cómo cambia tu neto."))

    kwargs = {}
    if plat_id == "upwork":
        tramo = st.selectbox("Historial con el cliente (Upwork)",
                             list(UPWORK_TRAMOS), format_func=lambda x: UPWORK_TRAMOS[x])
        kwargs["tipo_upwork"] = tramo

    r = calcular_neto_plataforma(valor_usd, plat_id, trm, **kwargs)

    bruto_cop = valor_usd * trm
    md(seccion("Resultado", r["descripcion"]))
    md(fila_cards([
        card("Recibes (neto)", ui.fmt_cop(r["valor_cop"]),
             badge(f"costo {r['costo_total_pct']:.1f}%", COLORS["gold"]),
             COLORS["green"]),
        card("Comisión total", ui.fmt_usd(r["comision_usd"]),
             f"≈ {ui.fmt_cop(r['comision_usd'] * trm)}", COLORS["red"]),
        card("TRM efectiva", ui.fmt_cop(r["trm_efectiva"]),
             f"spread {r['spread_fx_pct']*100:.1f}%", COLORS["blue"]),
    ]))

    # Desglose visual: del bruto teórico al neto recibido
    md(seccion("De US$ a COP", "A dónde va cada peso"))
    md(barra_h("Valor bruto (USD × TRM)", bruto_cop, bruto_cop,
               COLORS["muted"], ui.fmt_cop(bruto_cop)))
    md(barra_h("Comisión de plataforma", r["comision_usd"] * trm, bruto_cop,
               COLORS["red"], ui.fmt_cop(r["comision_usd"] * trm)))
    md(barra_h("Pérdida por spread FX", bruto_cop * r["spread_fx_pct"], bruto_cop,
               COLORS["gold"], ui.fmt_cop(round(bruto_cop * r["spread_fx_pct"]))))
    md(barra_h("Neto que recibes", r["valor_cop"], bruto_cop,
               COLORS["green"], ui.fmt_cop(r["valor_cop"])))

    if r["notas"]:
        st.caption(f"ℹ️ {r['notas']}")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · COMPARADOR
# ─────────────────────────────────────────────────────────────────────────────
def pagina_comparador(trm_info: dict):
    md("<div style='font-size:26px;font-weight:700'>🔄 Comparador de plataformas</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>Cuál te deja más pesos "
       "para un mismo pago en dólares.</div>")

    col1, col2 = st.columns([1, 1])
    with col1:
        valor_usd = st.slider("Monto del cliente (USD)", 50, 10_000, 1_000, 50,
                              key="cmp_usd")
    with col2:
        trm = st.number_input("TRM USD/COP", 2_000.0, 8_000.0,
                              float(trm_info["trm"]), 10.0, key="cmp_trm")

    tramo = st.selectbox("Historial Upwork", list(UPWORK_TRAMOS),
                         format_func=lambda x: UPWORK_TRAMOS[x], key="cmp_up")

    comp = comparar_plataformas(valor_usd, trm, tramo)
    mejor, peor = comp[0], comp[-1]
    ahorro = mejor["valor_cop"] - peor["valor_cop"]

    md(seccion("Mejor opción", ""))
    md(fila_cards([
        card("Ganadora", mejor["plataforma"],
             badge("recomendada", COLORS["green"]), COLORS["green"]),
        card("Recibes", ui.fmt_cop(mejor["valor_cop"]),
             f"costo {mejor['costo_total_pct']:.1f}%", COLORS["green"]),
        card("Ahorro vs. peor", ui.fmt_cop(ahorro),
             f"frente a {peor['plataforma']}", COLORS["gold"]),
    ]))

    # Gráfico Plotly de barras horizontales
    md(seccion("Neto por plataforma", f"Para US$ {valor_usd:,} a TRM {ui.fmt_cop(trm)}"))
    fig = ui.plotly_barras_h(
        [r["plataforma"] for r in comp],
        [r["valor_cop"] for r in comp],
        color=COLORS["green"], fmt="$,.0f",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # Tabla interactiva con barras de color (ProgressColumn)
    md(seccion("Detalle", "«vs mejor» = cuánto pierdes frente a la ganadora"))
    mejor_cop = mejor["valor_cop"]
    df = pd.DataFrame([{
        "Plataforma": r["plataforma"],
        "Neto COP": r["valor_cop"],
        "vs mejor": r["valor_cop"] - mejor_cop,
        "Comisión USD": r["comision_usd"],
        "Costo %": r["costo_total_pct"],
        "TRM efectiva": r["trm_efectiva"],
    } for r in comp])
    estilo = df.style.map(
        lambda v: f"color:{COLORS['red']};font-weight:600" if v < 0 else "",
        subset=["vs mejor"],
    )
    st.dataframe(
        estilo, width="stretch", hide_index=True,
        column_config={
            "Neto COP": st.column_config.ProgressColumn(
                "Neto COP", format="$%d",
                min_value=0, max_value=int(mejor_cop)),
            "vs mejor": st.column_config.NumberColumn("vs mejor", format="$%d"),
            "Comisión USD": st.column_config.NumberColumn(format="$%.2f"),
            "Costo %": st.column_config.NumberColumn(format="%.2f%%"),
            "TRM efectiva": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · CALCULADORA INVERSA
# ─────────────────────────────────────────────────────────────────────────────
def pagina_calculadora(trm_info: dict):
    md("<div style='font-size:26px;font-weight:700'>🧮 Calculadora inversa</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>¿Cuánto debes cobrar para "
       "recibir un neto objetivo, después de impuestos y comisiones?</div>")

    col1, col2 = st.columns([1, 1])
    with col1:
        neto_deseado = st.number_input("Neto que quieres recibir (COP)",
                                       100_000, 500_000_000, 5_000_000, 100_000)
        tipo = st.selectbox("Tipo de servicio", list(TIPOS_SERVICIO),
                            format_func=lambda x: TIPOS_SERVICIO[x])
    with col2:
        es_declarante = st.toggle("Declaro renta", value=False)
        incluir_aportes = st.toggle("Incluir aportes a salud y pensión", value=True)

    usar_plat = st.toggle("Cobro por una plataforma internacional (USD)", value=False)
    plat_id, trm = None, None
    if usar_plat:
        cpa, cpb = st.columns([1, 1])
        with cpa:
            plat_id = st.selectbox("Plataforma", [p["id"] for p in PLATAFORMAS],
                                   format_func=lambda x: PLAT_NOMBRES[x],
                                   key="inv_plat")
        with cpb:
            trm = st.number_input("TRM USD/COP", 2_000.0, 8_000.0,
                                  float(trm_info["trm"]), 10.0, key="inv_trm")

    r = calcular_bruto_necesario(
        neto_deseado, tipo, es_declarante, incluir_aportes,
        plataforma=plat_id, trm=trm,
    )

    md(seccion("Lo que debes facturar", ""))
    tarjetas = [
        card("Factura bruta (COP)", ui.fmt_cop(r["bruto_necesario"]),
             badge("antes de descuentos", COLORS["blue"]), COLORS["blue"]),
        card("Neto que recibirás", ui.fmt_cop(r["neto_real"]),
             f"objetivo {ui.fmt_cop(r['neto_deseado'])}", COLORS["green"]),
    ]
    if r.get("tiene_plataforma"):
        tarjetas.append(card(
            "Cobra al cliente (USD)", ui.fmt_usd(r["bruto_usd_necesario"]),
            badge(PLAT_NOMBRES.get(plat_id, ""), COLORS["gold"]), COLORS["gold"]))
    md(fila_cards(tarjetas))

    # Desglose del bruto al neto, en una tabla HTML clara
    bruto = r["bruto_necesario"]
    dg = r["desglose"]
    filas = [
        ("Factura bruta", ui.fmt_cop(bruto), C["text"], "600"),
        ("− Retención en la fuente (anticipo de renta)",
         "− " + ui.fmt_cop(dg["valor_retenido"]), C["red"], "500"),
    ]
    if dg.get("total_aportes"):
        filas.append(("− Aportes a salud y pensión",
                      "− " + ui.fmt_cop(dg["total_aportes"]), C["gold"], "500"))
    filas.append(("= Neto que recibes", ui.fmt_cop(dg["neto"]), C["green"], "700"))

    md(seccion("Cómo se reparte tu factura", "Del bruto facturado a tu bolsillo"))
    cuerpo = "".join(
        f"<tr style='border-bottom:1px solid {C['border']}'>"
        f"<td style='padding:9px 14px;color:{C['muted']};font-size:13px'>{etq}</td>"
        f"<td style='padding:9px 14px;text-align:right;color:{col};font-weight:{peso};"
        f"font-variant-numeric:tabular-nums'>{val}</td></tr>"
        for etq, val, col, peso in filas
    )
    md(f"<table style='width:100%;border-collapse:collapse;background:{C['card']};"
       f"border:1px solid {C['border']};border-radius:10px;overflow:hidden'>"
       f"{cuerpo}</table>")
    st.caption("La retención en la fuente es un anticipo del impuesto de renta: "
               "si declaras, se cruza al presentar tu declaración (Art. 365 ET).")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · PROYECCIÓN
# ─────────────────────────────────────────────────────────────────────────────
def pagina_proyeccion(trm_info: dict):
    md("<div style='font-size:26px;font-weight:700'>📈 Proyección anual</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>Tu ingreso real al año con "
       "retención, aportes e impuesto de renta (Art. 241 ET).</div>")

    modo = st.radio("Ingreso mensual en", ["COP", "USD (con plataforma)"],
                    horizontal=True)
    col1, col2 = st.columns([1, 1])

    if modo == "COP":
        with col1:
            ingreso = st.number_input("Ingreso mensual (COP)",
                                      500_000, 200_000_000, 6_000_000, 100_000)
            tipo = st.selectbox("Tipo de servicio", list(TIPOS_SERVICIO),
                               format_func=lambda x: TIPOS_SERVICIO[x], key="pry_tipo")
        with col2:
            es_declarante = st.toggle("Declaro renta", value=True, key="pry_decl")
            meses = st.slider("Meses a proyectar", 1, 12, 12)
        proy = proyeccion_anual(ingreso, tipo, es_declarante, meses=meses)
        sub = f"{ui.fmt_cop(ingreso)} / mes · {meses} meses"
    else:
        with col1:
            ingreso_usd = st.number_input("Ingreso mensual (USD)",
                                          100, 100_000, 2_000, 100)
            plat_id = st.selectbox("Plataforma de cobro",
                                   [p["id"] for p in PLATAFORMAS],
                                   format_func=lambda x: PLAT_NOMBRES[x], key="pry_plat")
        with col2:
            trm = st.number_input("TRM USD/COP", 2_000.0, 8_000.0,
                                  float(trm_info["trm"]), 10.0, key="pry_trm")
            es_declarante = st.toggle("Declaro renta", value=True, key="pry_decl2")
            meses = st.slider("Meses a proyectar", 1, 12, 12, key="pry_meses")
        proy = proyeccion_desde_usd(ingreso_usd, trm, plat_id,
                                    es_declarante=es_declarante, meses=meses)
        sub = (f"US$ {ingreso_usd:,} / mes · {PLAT_NOMBRES[plat_id]} · "
               f"{meses} meses")

    md(seccion("Resumen anual", sub))
    md(fila_cards([
        card("Ingreso bruto", ui.fmt_cop(proy["ingreso_bruto_anual"]),
             f"{meses} meses", COLORS["blue"]),
        card("Neto disponible", ui.fmt_cop(proy["neto_anual"]),
             badge(f"{proy['neto_pct_bruto']:.0f}% del bruto", COLORS["green"]),
             COLORS["green"]),
        card("Impuesto de renta", ui.fmt_cop(proy["impuesto_renta_estimado"]),
             f"tasa efectiva {proy['tasa_renta_efectiva_pct']:.1f}%", COLORS["red"]),
        card("Aportes SS (año)", ui.fmt_cop(proy["total_aportes_anual"]),
             "salud + pensión", COLORS["gold"]),
    ]))

    cga, cgb = st.columns([3, 2])
    with cga:
        # Área acumulada del neto mes a mes
        meses_x = list(range(1, proy["meses_proyectados"] + 1))
        neto_mes = proy["neto_mensual_promedio"]
        acum = [neto_mes * m for m in meses_x]
        fig = ui.plotly_area(
            [f"Mes {m}" for m in meses_x], acum,
            titulo="Neto disponible acumulado", color=COLORS["green"],
            nombre="Acumulado",
        )
        st.plotly_chart(fig, width="stretch",
                        config={"displayModeBar": False})
    with cgb:
        # Composición del bruto
        fig2 = ui.plotly_donut(
            ["Neto disponible", "Aportes SS", "Impuesto renta"],
            [proy["neto_anual"], proy["total_aportes_anual"],
             proy["impuesto_renta_estimado"]],
            titulo="Composición del bruto",
            colores=[COLORS["green"], COLORS["gold"], COLORS["red"]],
        )
        st.plotly_chart(fig2, width="stretch",
                        config={"displayModeBar": False})

    st.caption("Basado en tabla Art. 241 ET, UVT 2026 = $52.374 "
               "(Resolución DIAN 000238 de 2025). No constituye asesoría tributaria.")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · FACTURA
# ─────────────────────────────────────────────────────────────────────────────
def pagina_factura():
    md("<div style='font-size:26px;font-weight:700'>🧾 Generar factura PDF</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>Completa los datos y "
       "descarga un documento profesional listo para enviar.</div>")

    with st.form("form_factura"):
        st.markdown("**Emisor (tú)**")
        e1, e2 = st.columns(2)
        nombre_f = e1.text_input("Nombre / razón social", "Ana García")
        nit_f = e2.text_input("NIT o cédula", "52.123.456-7")
        e3, e4, e5 = st.columns(3)
        ciudad = e3.text_input("Ciudad", "Bogotá")
        email = e4.text_input("Email", "ana@ejemplo.co")
        telefono = e5.text_input("Teléfono", "")

        st.markdown("**Cliente**")
        c1, c2 = st.columns(2)
        nombre_c = c1.text_input("Nombre del cliente", "Tech Corp SAS")
        nit_c = c2.text_input("NIT del cliente", "900.123.456-7")

        st.markdown("**Servicio**")
        descripcion = st.text_area("Descripción del servicio",
                                   "Desarrollo de API de pagos — Sprint 3")
        s1, s2 = st.columns(2)
        valor = s1.number_input("Valor (COP)", 0, 1_000_000_000, 5_000_000, 50_000)
        retencion = s2.number_input("Retención en la fuente (%)", 0.0, 20.0, 11.0, 0.5)

        st.markdown("**Documento**")
        d1, d2 = st.columns(2)
        num_sugerido = (f"FCO-{date.today().year}-"
                        f"{str(st.session_state.get('factura_count', 1)).zfill(3)}")
        numero = d1.text_input("N.º de factura", num_sugerido)
        fecha = d2.date_input("Fecha", date.today())

        with st.expander("Datos de pago (opcional)"):
            p1, p2 = st.columns(2)
            forma_pago = p1.selectbox(
                "Forma de pago",
                ["Transferencia bancaria", "Nequi", "Daviplata", "Cripto",
                 "Efectivo", "Otro"])
            banco = p2.text_input("Banco", "")
            p3, p4 = st.columns(2)
            cuenta = p3.text_input("N.º de cuenta", "")
            tipo_cuenta = p4.selectbox("Tipo de cuenta", ["Ahorros", "Corriente"])
            notas = st.text_area("Notas al pie", "Pago a 15 días.")

        generar = st.form_submit_button("📄 Generar factura PDF")

    # Vista previa del desglose (siempre que haya datos mínimos)
    if valor > 0 and descripcion.strip():
        try:
            datos_prev = {
                "nombre_freelancer": nombre_f or "—", "nit_freelancer": nit_f or "—",
                "nombre_cliente": nombre_c or "—", "nit_cliente": nit_c or "—",
                "descripcion_servicio": descripcion, "valor_cop": valor,
                "retencion_pct": retencion,
            }
            dg = _desglose_factura(datos_prev)
            md(seccion("Vista previa", f"Factura {dg['numero']} · {dg['fecha_str']}"))
            md(fila_cards([
                card("Subtotal", ui.fmt_cop(dg["subtotal"]), "", COLORS["blue"]),
                card("Retención", "- " + ui.fmt_cop(dg["retencion_valor"]),
                     f"{dg['retencion_pct']*100:.0f}%", COLORS["red"]),
                card("Total a pagar", ui.fmt_cop(dg["total"]),
                     badge("neto cliente", COLORS["green"]), COLORS["green"]),
            ]))
        except ValueError as exc:
            st.warning(str(exc))

    if generar:
        obligatorios = {
            "Nombre / razón social": nombre_f,
            "NIT o cédula": nit_f,
            "Nombre del cliente": nombre_c,
            "NIT del cliente": nit_c,
            "Descripción del servicio": descripcion,
        }
        faltan = [campo for campo, val in obligatorios.items() if not str(val).strip()]
        if faltan:
            st.error("Faltan campos obligatorios: " + ", ".join(faltan))
        elif valor <= 0:
            st.error("El valor de la factura debe ser mayor a $0.")
        else:
            datos = {
                "nombre_freelancer": nombre_f, "nit_freelancer": nit_f,
                "nombre_cliente": nombre_c, "nit_cliente": nit_c,
                "descripcion_servicio": descripcion, "valor_cop": valor,
                "retencion_pct": retencion, "numero_factura": numero,
                "fecha": fecha, "ciudad": ciudad, "email": email,
                "telefono": telefono, "banco": banco, "cuenta": cuenta,
                "tipo_cuenta": tipo_cuenta, "forma_de_pago": forma_pago,
                "notas": notas.strip(),
            }
            try:
                pdf_bytes = generar_factura(datos)
                st.session_state["factura_count"] = (
                    st.session_state.get("factura_count", 1) + 1)
                st.success("Factura generada correctamente.")
                st.balloons()
                st.download_button(
                    "⬇️ Descargar PDF", data=pdf_bytes,
                    file_name=f"{numero or 'factura'}.pdf", mime="application/pdf",
                )
            except ValueError as exc:
                st.error(f"No se pudo generar la factura: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# PÁGINA · CUENTA DE COBRO
# ─────────────────────────────────────────────────────────────────────────────
def pagina_cuenta_cobro():
    md("<div style='font-size:26px;font-weight:700'>📄 Cuenta de cobro</div>")
    md(f"<div style='color:{C['muted']};font-size:14px'>El documento equivalente "
       "para personas naturales no obligadas a facturar electrónicamente "
       "(Resolución DIAN 000042 de 2020).</div>")

    with st.form("form_cuenta_cobro"):
        st.markdown("**Cobrado por (tú)**")
        f1, f2 = st.columns(2)
        nombre_f = f1.text_input("Nombre completo", "Ana García", key="cc_nombre")
        cedula_f = f2.text_input("Cédula", "52.123.456", key="cc_cedula")
        f3, f4, f5 = st.columns(3)
        ciudad_f = f3.text_input("Ciudad", "Bogotá", key="cc_ciudad")
        email_f = f4.text_input("Email", "ana@ejemplo.co", key="cc_email")
        telefono_f = f5.text_input("Teléfono", "", key="cc_tel")

        st.markdown("**Cobrado a (cliente)**")
        c1, c2 = st.columns(2)
        empresa_c = c1.text_input("Razón social", "Tech Corp SAS", key="cc_empresa")
        nit_c = c2.text_input("NIT", "900.123.456-7", key="cc_nit")
        c3, c4 = st.columns(2)
        contacto_c = c3.text_input("Contacto", "", key="cc_contacto")
        ciudad_c = c4.text_input("Ciudad del cliente", "", key="cc_ciudad_cli")

        st.markdown("**Servicio**")
        descripcion = st.text_area("Descripción del servicio",
                                   "Consultoría en transformación digital — junio",
                                   key="cc_desc")
        s1, s2 = st.columns(2)
        valor = s1.number_input("Valor bruto (COP)", 0, 1_000_000_000,
                                5_000_000, 50_000, key="cc_valor")
        retencion_pct = s2.number_input("Retención en la fuente (%)", 0.0, 20.0,
                                        11.0, 0.5, key="cc_ret")

        st.markdown("**Documento**")
        d1, d2 = st.columns(2)
        num_sugerido = (f"CC-{date.today().year}-"
                        f"{str(st.session_state.get('cc_count', 1)).zfill(3)}")
        numero = d1.text_input("N.º de documento", num_sugerido, key="cc_num")
        fecha = d2.date_input("Fecha", date.today(), key="cc_fecha")

        incluir_retencion = st.toggle("Aplicar retención en la fuente",
                                      value=True, key="cc_inc_ret")
        incluir_aportes = st.toggle(
            "Incluir aportes a salud y pensión (informativo)",
            value=False, key="cc_inc_ap")

        with st.expander("Datos bancarios (opcional)"):
            b1, b2 = st.columns(2)
            banco = b1.text_input("Banco", "", key="cc_banco")
            tipo_cuenta = b2.selectbox("Tipo de cuenta", ["Ahorros", "Corriente"],
                                       key="cc_tipo")
            cuenta = st.text_input("N.º de cuenta", "", key="cc_cuenta")

        generar = st.form_submit_button("📄 Generar cuenta de cobro")

    # Vista previa del desglose (siempre que haya datos mínimos)
    if valor > 0 and descripcion.strip():
        tarifa = retencion_pct / 100.0
        valor_retencion = round(valor * tarifa) if incluir_retencion else 0
        neto = valor - valor_retencion
        md(seccion("Vista previa", f"Documento {numero}"))
        md(fila_cards([
            card("Valor bruto", ui.fmt_cop(valor), "", COLORS["blue"]),
            card("Retención", "- " + ui.fmt_cop(valor_retencion),
                 f"{retencion_pct:.0f}%" if incluir_retencion else "no aplica",
                 COLORS["red"]),
            card("Neto a pagar", ui.fmt_cop(neto),
                 badge("recibe el freelancer", COLORS["green"]), COLORS["green"]),
        ]))
        if incluir_aportes:
            ap = calcular_aportes(valor)
            md(seccion("Aportes a seguridad social", "A cargo del prestador (IBC 40%)"))
            md(fila_cards([
                card("Salud (12.5%)", ui.fmt_cop(ap["aporte_salud"]), "", COLORS["gold"]),
                card("Pensión (16%)", ui.fmt_cop(ap["aporte_pension"]), "", COLORS["gold"]),
                card("Total aportes", ui.fmt_cop(ap["total_aportes"]),
                     badge("mensual", COLORS["gold"]), COLORS["gold"]),
            ]))

    if generar:
        obligatorios = {
            "Nombre completo": nombre_f,
            "Cédula": cedula_f,
            "Razón social": empresa_c,
            "NIT": nit_c,
            "Descripción del servicio": descripcion,
        }
        faltan = [campo for campo, val in obligatorios.items() if not str(val).strip()]
        if faltan:
            st.error("Faltan campos obligatorios: " + ", ".join(faltan))
            return
        if valor <= 0:
            st.error("El valor de la cuenta de cobro debe ser mayor a $0.")
            return

        datos_freelancer = {"nombre": nombre_f, "cedula": cedula_f}
        for clave, val in (("ciudad", ciudad_f), ("email", email_f),
                           ("telefono", telefono_f), ("banco", banco),
                           ("tipo_cuenta", tipo_cuenta), ("cuenta", cuenta)):
            if str(val).strip():
                datos_freelancer[clave] = val
        datos_cliente = {"empresa": empresa_c, "nit": nit_c}
        for clave, val in (("contacto", contacto_c), ("ciudad", ciudad_c)):
            if str(val).strip():
                datos_cliente[clave] = val

        kwargs = {}
        if incluir_aportes:
            ap = calcular_aportes(valor)
            kwargs.update(incluir_aportes=True,
                          aporte_salud=ap["aporte_salud"],
                          aporte_pension=ap["aporte_pension"])

        pdf_bytes = generar_cuenta_cobro(
            datos_freelancer=datos_freelancer,
            datos_cliente=datos_cliente,
            valor=valor,
            descripcion=descripcion,
            numero=numero or None,
            fecha=fecha,
            incluir_retencion=incluir_retencion,
            tarifa_retencion=retencion_pct / 100.0,
            **kwargs,
        )
        st.session_state["cc_count"] = st.session_state.get("cc_count", 1) + 1
        st.success("Cuenta de cobro generada correctamente.")
        st.balloons()
        st.download_button(
            "⬇️ Descargar cuenta de cobro", data=pdf_bytes,
            file_name=f"{numero or 'cuenta_cobro'}.pdf", mime="application/pdf",
        )


# ─────────────────────────────────────────────────────────────────────────────
# NAVEGACIÓN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    with st.sidebar:
        md(f"<div style='font-size:22px;font-weight:700;padding:4px 0 2px'>"
           f"🧾 factura&#8209;co</div>"
           f"<div style='color:{C['muted']};font-size:12px;margin-bottom:14px'>"
           f"Finanzas freelancer · Colombia</div>")
        pagina = st.radio(
            "Navegación",
            ["🏠 Inicio", "💱 Plataformas", "🔄 Comparador",
             "🧮 Calculadora", "📈 Proyección", "🧾 Factura",
             "📄 Cuenta de cobro"],
            label_visibility="collapsed",
        )
        st.divider()
        trm_info = trm_info_cached()
        md(f"<div style='color:{C['muted']};font-size:11px'>TRM hoy</div>"
           f"<div style='font-size:18px;font-weight:700;font-variant-numeric:"
           f"tabular-nums'>{ui.fmt_cop(trm_info['trm'])}</div>"
           f"<div style='color:{C['muted']};font-size:10px;margin-top:2px'>"
           f"{trm_info['fuente']}</div>")
        md(f"<div style='position:relative;margin-top:18px;color:{C['muted']};"
           f"font-size:10px'>v{__version__}</div>")

    if pagina.endswith("Inicio"):
        pagina_inicio(trm_info)
    elif pagina.endswith("Plataformas"):
        pagina_plataformas(trm_info)
    elif pagina.endswith("Comparador"):
        pagina_comparador(trm_info)
    elif pagina.endswith("Calculadora"):
        pagina_calculadora(trm_info)
    elif pagina.endswith("Proyección"):
        pagina_proyeccion(trm_info)
    elif pagina.endswith("Factura"):
        pagina_factura()
    elif pagina.endswith("Cuenta de cobro"):
        pagina_cuenta_cobro()


if __name__ == "__main__":
    main()
