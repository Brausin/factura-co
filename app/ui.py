"""
ui.py — Sistema de diseño "Glassmorphism fintech 2026" para factura-co.

Centraliza la paleta, el CSS global y los componentes visuales reutilizables
(tarjetas de vidrio, barras, badges, secciones, iconos SVG) y los gráficos
Plotly tematizados. La app (`app/main.py`) importa de aquí para mantener una
estética coherente sin depender de los widgets por defecto.

Sistema de diseño (ui-ux-pro-max · Glassmorphism + paleta "Gold trust
+ profit green", rev. 2026-06 — ver design-system/factura-co/MASTER.md):
    - Fondo slate profundo #0F172A con mesh gradient aurora (oro/cian/esmeralda)
      fijo, sutil y sin animación.
    - Tarjetas de vidrio esmerilado: rgba blanca translúcida, backdrop-filter
      blur 14px, borde 1px rgba(255,255,255,.14) y reflejo superior.
    - Acento primario oro #F59E0B; CTA esmeralda #10B981 (semántica de dinero;
      la skill marca los gradientes morados "AI" como anti-patrón fintech);
      info cian #38BDF8.
    - Tipografía DM Sans; números siempre con tabular-nums; separadores es-CO
      (punto de miles) también dentro de los gráficos Plotly.
    - Iconos SVG inline (trazo Lucide), nunca emojis como iconos.
    - Hover por borde/sombra sin layout shift (150–250 ms), focus visible,
      prefers-reduced-motion respetado, cursor pointer en lo clickeable.
    - Nunca usar st.metric / st.bar_chart / matplotlib.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

# ── Paleta de marca (Glassmorphism · Gold trust + profit green) ──────────────
COLORS = {
    "bg": "#0F172A",          # slate profundo
    "card": "rgba(255,255,255,0.055)",   # vidrio esmerilado
    "card_solid": "#16213D",  # respaldo sólido (donde el blur no aplica)
    "input": "rgba(15,23,42,0.55)",
    "border": "rgba(255,255,255,0.14)",
    "gold": "#F59E0B",        # primario / mejor opción / neto
    "amber": "#FBBF24",       # advertencias / costos
    "cta": "#10B981",         # CTA esmeralda (acciones, foco de inputs)
    "violet": "#8B5CF6",      # tono de apoyo (solo mesh de fondo, nunca CTA)
    "sky": "#38BDF8",         # informativo
    "red": "#F87171",         # negativo / retenciones
    "ok": "#34D399",          # estado correcto (semántico)
    "text": "#F8FAFC",
    "muted": "#A3B2CC",
}

_GRID = "rgba(165,180,205,0.14)"
_FONT = "'DM Sans','Segoe UI',sans-serif"


def _rgba(hex6: str, alpha: float) -> str:
    """Convierte ``#RRGGBB`` + alpha (0–1) a ``rgba(r,g,b,a)``."""
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Iconos SVG (trazo estilo Lucide, viewBox 24×24) ──────────────────────────
ICONS = {
    "home": "<path d='M3 9.5 12 3l9 6.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z'/>"
            "<path d='M9 22V12h6v10'/>",
    "wallet": "<path d='M21 12V7H5a2 2 0 0 1 0-4h14v4'/>"
              "<path d='M3 5v14a2 2 0 0 0 2 2h16v-5'/>"
              "<path d='M18 12a2 2 0 0 0 0 4h4v-4Z'/>",
    "repeat": "<path d='m17 2 4 4-4 4'/><path d='M3 11v-1a4 4 0 0 1 4-4h14'/>"
              "<path d='m7 22-4-4 4-4'/><path d='M21 13v1a4 4 0 0 1-4 4H3'/>",
    "calculator": "<rect x='4' y='2' width='16' height='20' rx='2'/>"
                  "<line x1='8' y1='6' x2='16' y2='6'/>"
                  "<line x1='16' y1='14' x2='16' y2='18'/>"
                  "<path d='M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01"
                  "M8 18h.01M12 18h.01'/>",
    "trending-up": "<polyline points='22 7 13.5 15.5 8.5 10.5 2 17'/>"
                   "<polyline points='16 7 22 7 22 13'/>",
    "file-text": "<path d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 "
                 "2-2V7Z'/><path d='M14 2v4a2 2 0 0 0 2 2h4'/>"
                 "<path d='M16 13H8M16 17H8M10 9H8'/>",
    "receipt": "<path d='M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 "
               "1-2-1-2 1-2-1-2 1Z'/>"
               "<path d='M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8'/>"
               "<path d='M12 17.5v-11'/>",
    "shield-check": "<path d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 "
                    "20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1 1 0 0 "
                    "1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/>"
                    "<path d='m9 12 2 2 4-4'/>",
    "download": "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/>"
                "<polyline points='7 10 12 15 17 10'/>"
                "<line x1='12' y1='15' x2='12' y2='3'/>",
    "zap": "<path d='M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 "
           "6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 "
           "1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z'/>",
    "info": "<circle cx='12' cy='12' r='10'/><path d='M12 16v-4M12 8h.01'/>",
    "check-circle": "<path d='M21.8 10A10 10 0 1 1 17 3.34'/>"
                    "<path d='m9 11 3 3L22 4'/>",
    "alert-triangle": "<path d='m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 "
                      "4 21h16a2 2 0 0 0 1.73-3Z'/><path d='M12 9v4M12 17h.01'/>",
    "chart-bar": "<path d='M3 3v16a2 2 0 0 0 2 2h16'/>"
                 "<path d='M7 16v-3M12 16v-8M17 16v-5'/>",
    "sparkles": "<path d='M12 3l1.9 5.7a2 2 0 0 0 1.3 1.3L21 12l-5.8 1.9a2 2 0 0 "
                "0-1.3 1.3L12 21l-1.9-5.8a2 2 0 0 0-1.3-1.3L3 12l5.8-1.9a2 2 0 0 "
                "0 1.3-1.3Z'/>",
}


def icono(nombre: str, size: int = 20, color: str = COLORS["text"]) -> str:
    """Icono SVG inline (trazo 2px, estilo Lucide)."""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"stroke='{color}' stroke-width='2' stroke-linecap='round' "
        f"stroke-linejoin='round' style='flex-shrink:0;vertical-align:-3px'>"
        f"{ICONS[nombre]}</svg>"
    )


# ── Formateo numérico ────────────────────────────────────────────────────────
def fmt_cop(valor: float, simbolo: bool = True) -> str:
    """Formatea pesos colombianos: ``$ 4.450.000``."""
    s = f"{valor:,.0f}".replace(",", ".")
    return f"$ {s}" if simbolo else s


def fmt_usd(valor: float) -> str:
    """Formatea dólares: ``US$ 1,250.00``."""
    return f"US$ {valor:,.2f}"


# ── CSS global ───────────────────────────────────────────────────────────────
def apply_styles(C: dict = COLORS) -> None:
    """Inyecta el CSS global: mesh aurora, vidrio, inputs, botones, nav."""
    st.markdown(
        f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&display=swap');
    * {{font-family:{_FONT}!important}}
    #MainMenu,footer,header {{visibility:hidden}}
    .block-container {{padding-top:1.3rem;padding-bottom:3rem;max-width:1180px}}

    /* Fondo: slate profundo con mesh gradient aurora fijo (sin morado-CTA) */
    .stApp {{
        background:
            radial-gradient(58% 42% at 12% 0%, {_rgba('#8B5CF6', .10)}, transparent 70%),
            radial-gradient(45% 38% at 90% 8%, {_rgba('#F59E0B', .13)}, transparent 70%),
            radial-gradient(70% 55% at 50% 110%, {_rgba('#10B981', .10)}, transparent 70%),
            {C['bg']} !important;
        background-attachment: fixed !important;
    }}
    h1,h2,h3,h4,p,span,label,div {{color:{C['text']}}}
    ::selection {{background:{_rgba('#10B981', .40)}}}
    ::-webkit-scrollbar {{width:10px;height:10px}}
    ::-webkit-scrollbar-track {{background:transparent}}
    ::-webkit-scrollbar-thumb {{background:rgba(165,180,205,.25);border-radius:6px}}
    ::-webkit-scrollbar-thumb:hover {{background:rgba(165,180,205,.4)}}

    /* Inputs de vidrio */
    .stTextInput input,.stNumberInput input,.stDateInput input,
    textarea,.stTextArea textarea {{
        background:{C['input']}!important;color:{C['text']}!important;
        border:1px solid {C['border']}!important;border-radius:10px!important;
        transition:border-color 180ms ease,box-shadow 180ms ease!important}}
    .stTextInput input:focus,.stNumberInput input:focus,
    .stDateInput input:focus,.stTextArea textarea:focus {{
        border-color:{C['cta']}!important;
        box-shadow:0 0 0 2px {_rgba('#10B981', .30)}!important}}
    .stNumberInput button {{
        background:transparent!important;color:{C['muted']}!important;
        cursor:pointer!important}}
    .stNumberInput button:hover {{color:{C['text']}!important}}
    div[data-baseweb="select"]>div {{
        background:{C['input']}!important;border:1px solid {C['border']}!important;
        border-radius:10px!important;color:{C['text']}!important;
        cursor:pointer!important;
        transition:border-color 180ms ease!important}}
    div[data-baseweb="select"]>div:hover {{border-color:{_rgba('#10B981', .55)}!important}}
    ul[data-testid="stSelectboxVirtualDropdown"] {{
        background:#1B2542!important;border:1px solid {C['border']}!important}}
    li[role="option"] {{cursor:pointer!important}}

    /* Botones: CTA esmeralda con glow (anti-patrón fintech: nada de morado) */
    .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button {{
        background:linear-gradient(135deg,{C['cta']},#059669)!important;
        color:#04221A!important;border:1px solid {_rgba('#10B981', .5)}!important;
        border-radius:10px!important;font-weight:700!important;
        padding:.55rem 1.3rem!important;cursor:pointer!important;
        transition:box-shadow 200ms ease,filter 200ms ease!important}}
    .stButton>button:hover,.stDownloadButton>button:hover,
    .stFormSubmitButton>button:hover {{
        filter:brightness(1.10)!important;
        box-shadow:0 6px 24px {_rgba('#10B981', .40)}!important}}
    .stButton>button:focus-visible,.stDownloadButton>button:focus-visible,
    .stFormSubmitButton>button:focus-visible {{
        outline:2px solid {C['gold']}!important;outline-offset:2px!important}}

    /* Toggles y radios con acento esmeralda */
    .stCheckbox label,.stRadio label,.stToggle label {{cursor:pointer!important}}
    div[data-testid="stToggle"] label {{cursor:pointer!important}}
    .stTabs [aria-selected="true"] {{
        color:{C['text']}!important;border-bottom:2px solid {C['gold']}!important}}
    .stTabs button {{cursor:pointer!important}}

    /* Radio del área principal como control segmentado */
    section[data-testid="stMain"] .stRadio div[role="radiogroup"] {{gap:8px}}
    section[data-testid="stMain"] .stRadio label {{
        background:{C['card']};border:1px solid {C['border']};
        border-radius:20px;padding:4px 14px!important;cursor:pointer!important;
        transition:border-color 180ms ease,background 180ms ease!important}}
    section[data-testid="stMain"] .stRadio label:hover {{
        border-color:{_rgba('#10B981', .6)}}}
    section[data-testid="stMain"] .stRadio label:has(input:checked) {{
        background:{_rgba('#10B981', .20)};border-color:{C['cta']}}}
    section[data-testid="stMain"] .stRadio label:has(input:focus-visible) {{
        outline:2px solid {C['gold']};outline-offset:2px}}
    section[data-testid="stMain"] .stRadio label>div:first-child {{display:none!important}}

    /* Sidebar de vidrio: navegación tipo app */
    div[data-testid="stSidebar"] {{
        background:rgba(13,20,40,.78)!important;
        backdrop-filter:blur(18px)!important;-webkit-backdrop-filter:blur(18px)!important;
        border-right:1px solid {C['border']}!important}}
    div[data-testid="stSidebar"] .stRadio label {{
        display:flex!important;align-items:center;color:{C['muted']}!important;
        font-weight:500;padding:9px 13px!important;margin:2px 0!important;
        border-radius:10px!important;cursor:pointer!important;
        border:1px solid transparent!important;
        transition:background 160ms ease,color 160ms ease,border-color 160ms ease!important}}
    div[data-testid="stSidebar"] .stRadio label:hover {{
        background:{_rgba('#10B981', .10)}!important;color:{C['text']}!important}}
    div[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
        background:{_rgba('#F59E0B', .14)}!important;color:{C['text']}!important;
        border-color:{_rgba('#F59E0B', .4)}!important;
        box-shadow:inset 3px 0 0 {C['gold']}!important}}
    div[data-testid="stSidebar"] .stRadio label:has(input:checked) p {{
        font-weight:700!important}}
    div[data-testid="stSidebar"] .stRadio label:has(input:focus-visible) {{
        outline:2px solid {C['gold']}!important;outline-offset:1px!important}}
    div[data-testid="stSidebar"] .stRadio label>div:first-child {{display:none!important}}

    /* Expanders, código y tablas de vidrio */
    div[data-testid="stExpander"] {{
        background:{C['card']}!important;border:1px solid {C['border']}!important;
        border-radius:14px!important;
        backdrop-filter:blur(14px)!important;-webkit-backdrop-filter:blur(14px)!important}}
    div[data-testid="stExpander"] summary {{cursor:pointer!important}}
    /* Corrige textos superpuestos: el contenido de un expander cerrado se
       seguía pintando encima de lo que está debajo. */
    div[data-testid="stExpander"] details:not([open]) [data-testid="stExpanderDetails"] {{
        display:none!important}}
    div[data-testid="stExpander"] summary:focus-visible {{
        outline:2px solid {C['gold']}!important;outline-offset:2px!important}}
    .stDataFrame {{border:1px solid {C['border']}!important;border-radius:14px!important}}
    .stCode,div[data-testid="stCode"] pre,pre {{
        background:{_rgba('#0B1226', .85)}!important;
        border:1px solid {C['border']}!important;border-radius:12px!important}}
    pre code,code {{color:{C['text']}!important;
        font-family:'DM Mono','Cascadia Code',monospace!important;
        font-variant-numeric:tabular-nums}}
    hr {{border-color:{C['border']}!important}}
    .stCaption,.stCaption p,div[data-testid="stCaptionContainer"] p {{
        color:{C['muted']}!important}}
    .stAlert {{background:{C['card']}!important;
        border:1px solid {C['border']}!important;border-radius:12px!important;
        backdrop-filter:blur(10px)!important}}
    .stAlert p {{color:{C['text']}!important}}

    /* Slider: valor con números tabulares */
    .stSlider [data-testid="stSliderThumbValue"] {{
        font-variant-numeric:tabular-nums;color:{C['cta']}!important}}
    .stSlider [data-testid="stTickBar"] div {{color:{C['muted']}!important}}

    /* Tarjeta de vidrio reutilizable */
    .fco-card {{
        background:{C['card']};border:1px solid {C['border']};
        border-radius:16px;
        backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
        box-shadow:0 8px 32px rgba(2,6,23,.35),inset 0 1px 0 rgba(255,255,255,.07);
        transition:border-color 200ms ease,box-shadow 200ms ease}}
    .fco-card:hover {{
        border-color:rgba(255,255,255,.30);
        box-shadow:0 12px 40px rgba(2,6,23,.5),0 0 24px {_rgba('#10B981', .10)},
                   inset 0 1px 0 rgba(255,255,255,.09)}}

    .fco-num {{font-variant-numeric:tabular-nums}}

    /* Responsive: padding compacto en pantallas angostas */
    @media (max-width: 740px) {{
        .block-container {{padding-left:1rem;padding-right:1rem}}
    }}

    @media (prefers-reduced-motion: reduce) {{
        * {{transition:none!important;animation:none!important;
            scroll-behavior:auto!important}}
    }}
    </style>""",
        unsafe_allow_html=True,
    )


# ── Componentes HTML ─────────────────────────────────────────────────────────
def card(label: str, valor: str, delta: str = "",
         color: str = COLORS["gold"], bg: str | None = None) -> str:
    """Tarjeta KPI de vidrio: etiqueta, valor grande tabular, delta y acento."""
    d = (f"<span style='color:{color};font-size:12px;margin-top:5px;display:block'>"
         f"{delta}</span>") if delta else ""
    fondo = f"background:{bg};" if bg else ""
    return (
        f"<div class='fco-card' style=\"{fondo}padding:16px 20px;height:100%;"
        f"position:relative;overflow:hidden\">"
        f"<div style='position:absolute;inset:0 auto auto 0;width:100%;height:2px;"
        f"background:linear-gradient(90deg,{color},transparent 70%)'></div>"
        f"<div style=\"color:{COLORS['muted']};font-size:11px;font-weight:600;"
        f"text-transform:uppercase;letter-spacing:.08em\">{label}</div>"
        f"<div class='fco-num' style=\"color:{COLORS['text']};font-size:29px;"
        f"font-weight:700;margin:6px 0 2px\">{valor}</div>{d}</div>"
    )


def fila_cards(cards: list[str], gap: int = 12) -> str:
    """Envuelve varias tarjetas en una fila flex responsiva."""
    inner = "".join(f"<div style='flex:1;min-width:175px'>{c}</div>" for c in cards)
    return (f"<div style='display:flex;gap:{gap}px;flex-wrap:wrap;margin:6px 0'>"
            f"{inner}</div>")


def barra_h(label: str, valor: float, maximo: float,
            color: str = COLORS["sky"], detalle: str = "") -> str:
    """Barra horizontal de progreso con etiqueta y detalle a la derecha."""
    p = min(100, (valor / maximo) * 100) if maximo else 0
    return (
        f"<div style='margin:11px 0'>"
        f"<div style='display:flex;justify-content:space-between;gap:12px;"
        f"color:{COLORS['muted']};font-size:12.5px;margin-bottom:5px'>"
        f"<span style='font-weight:500'>{label}</span>"
        f"<span class='fco-num'>{detalle}</span></div>"
        f"<div style='background:rgba(165,180,205,.12);border-radius:6px;"
        f"height:9px;overflow:hidden'>"
        f"<div style='width:{p:.1f}%;background:linear-gradient(90deg,{color},"
        f"{color}99);height:9px;border-radius:6px;"
        f"box-shadow:0 0 10px {color}55;transition:width 400ms ease'></div>"
        f"</div></div>"
    )


def badge(texto: str, color: str = COLORS["gold"]) -> str:
    """Etiqueta tipo pill con color de acento."""
    return (
        f"<span style='background:{color}22;color:{color};border:1px solid {color}55;"
        f"border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600'>"
        f"{texto}</span>"
    )


def pill_estado(texto: str, tipo: str = "ok") -> str:
    """Pill de estado con punto de color (ok=esmeralda, alerta=ámbar, error=rojo)."""
    color = {"ok": COLORS["ok"], "alerta": COLORS["amber"],
             "error": COLORS["red"]}.get(tipo, COLORS["muted"])
    return (
        f"<span style='display:inline-flex;align-items:center;gap:6px;"
        f"background:{color}1A;color:{color};border:1px solid {color}44;"
        f"border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600'>"
        f"<svg width='8' height='8' viewBox='0 0 8 8' fill='{color}'>"
        f"<circle cx='4' cy='4' r='4'/></svg>{texto}</span>"
    )


def seccion(titulo: str, subtitulo: str = "") -> str:
    """Encabezado de sección con título y subtítulo opcional."""
    sub = (f"<div style='color:{COLORS['muted']};font-size:13px;margin-top:3px'>"
           f"{subtitulo}</div>") if subtitulo else ""
    return (f"<div style='margin:26px 0 14px'>"
            f"<div style='display:flex;align-items:center;gap:10px'>"
            f"<div style='width:4px;height:18px;border-radius:2px;"
            f"background:linear-gradient(180deg,{COLORS['gold']},{COLORS['cta']})'>"
            f"</div>"
            f"<div style='color:{COLORS['text']};font-size:18px;font-weight:700'>"
            f"{titulo}</div></div>{sub}</div>")


def titulo_pagina(icon: str, titulo: str, subtitulo: str = "") -> None:
    """Encabezado de página: chip de vidrio con icono dorado + título grande."""
    sub = (f"<div style='color:{COLORS['muted']};font-size:14px;margin-top:3px'>"
           f"{subtitulo}</div>") if subtitulo else ""
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:13px;margin:2px 0 8px'>"
        f"<div class='fco-card' style='border-radius:13px;padding:10px;display:flex'>"
        f"{icono(icon, 22, COLORS['gold'])}</div>"
        f"<div><div style='font-size:27px;font-weight:800;letter-spacing:-.02em'>"
        f"{titulo}</div>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def md(html: str) -> None:
    """Atajo para renderizar HTML custom."""
    st.markdown(html, unsafe_allow_html=True)


# ── Gráficos Plotly (tema glassmorphism oscuro) ──────────────────────────────
def _base_layout(fig: go.Figure, titulo: str = "", height: int = 350) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"],
                                          family="DM Sans")),
        margin=dict(l=0, r=80, t=40 if titulo else 10, b=0),
        height=height, font=dict(family="DM Sans", color=COLORS["muted"]),
        separators=",.",  # es-CO: coma decimal, punto de miles
        hoverlabel=dict(bgcolor="#1B2542", bordercolor="rgba(255,255,255,.2)",
                        font=dict(family="DM Sans", color=COLORS["text"])),
        showlegend=False,
    )
    return fig


def plotly_barras_h(labels, valores, titulo: str = "",
                    color: str = COLORS["gold"], fmt: str = "$,.0f",
                    resaltar_primero: bool = True) -> go.Figure:
    """Barras horizontales; resalta la primera (mejor opción) en dorado."""
    n = len(labels)
    colores = [color if (resaltar_primero and i == 0) else "rgba(165,180,205,.30)"
               for i in range(n)]
    fig = go.Figure(go.Bar(
        x=list(valores), y=list(labels), orientation="h",
        marker=dict(color=colores, line=dict(width=0)),
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:{fmt}}}<extra></extra>",
        text=[fmt_cop(v) for v in valores], textposition="outside",
        cliponaxis=False,
        textfont=dict(color=COLORS["muted"], size=11),
    ))
    _base_layout(fig, titulo, height=max(260, 46 * n + 60))
    fig.update_layout(
        xaxis=dict(gridcolor=_GRID, color=COLORS["muted"], tickformat=fmt,
                   showgrid=True, zeroline=False),
        yaxis=dict(color=COLORS["text"], tickfont=dict(size=12),
                   autorange="reversed"),
    )
    return fig


def plotly_area(x, y, titulo: str = "", color: str = COLORS["cta"],
                fmt: str = "$,.0f", nombre: str = "") -> go.Figure:
    """Área acumulada (p. ej. ingreso neto anual mes a mes)."""
    fig = go.Figure(go.Scatter(
        x=list(x), y=list(y), mode="lines+markers",
        line=dict(color=color, width=2.5, shape="spline"),
        marker=dict(color=color, size=6),
        fill="tozeroy", fillcolor=_rgba(color, 0.15),
        hovertemplate=(f"<b>%{{x}}</b><br>{nombre}: %{{y:{fmt}}}<extra></extra>"),
    ))
    _base_layout(fig, titulo, height=340)
    fig.update_layout(
        xaxis=dict(gridcolor=_GRID, color=COLORS["muted"], showgrid=False),
        yaxis=dict(gridcolor=_GRID, color=COLORS["muted"], tickformat=fmt,
                   showgrid=True, zeroline=False),
    )
    return fig


def plotly_donut(labels, valores, titulo: str = "",
                 colores: list | None = None) -> go.Figure:
    """Donut para composición (bruto → retención, aportes, neto)."""
    colores = colores or [COLORS["gold"], COLORS["red"],
                          COLORS["amber"], COLORS["sky"]]
    fig = go.Figure(go.Pie(
        labels=list(labels), values=list(valores), hole=0.62,
        marker=dict(colors=colores, line=dict(color=COLORS["bg"], width=2)),
        textinfo="percent", textfont=dict(family="DM Sans", size=12,
                                           color=COLORS["bg"]),
        hovertemplate="<b>%{label}</b><br>%{value:$,.0f} (%{percent})<extra></extra>",
    ))
    _base_layout(fig, titulo, height=340)
    fig.update_layout(margin=dict(l=0, r=0, t=40 if titulo else 10, b=10),
                      showlegend=True,
                      legend=dict(font=dict(color=COLORS["muted"], size=11),
                                  orientation="h", y=-0.12))
    return fig
