"""
ui.py — Sistema de diseño "dark finance 2026" para la app de factura-co.

Centraliza la paleta, el CSS global y los componentes visuales reutilizables
(tarjetas, barras, badges, secciones, iconos SVG) y los gráficos Plotly con
tema oscuro. La app (`app/main.py`) importa de aquí para mantener una estética
coherente y sin depender de los widgets por defecto que rompen el tema.

Sistema de diseño (ui-ux-pro-max · Dark Mode OLED + fintech):
    - Fondo profundo #020617, tarjetas slate, CTA verde #22C55E.
    - Tipografía IBM Plex Sans (mood financiero/profesional).
    - Iconos SVG inline (trazo Lucide), nunca emojis como iconos.
    - Hover sin saltos de layout (color/sombra, 150-200 ms).
    - Focus visible para teclado y respeto de prefers-reduced-motion.
    - Todo número tabular con `font-variant-numeric: tabular-nums`.
    - Nunca usar st.metric / st.bar_chart / matplotlib.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

# ── Paleta de marca (Dark OLED finance) ──────────────────────────────────────
COLORS = {
    "bg": "#020617",
    "card": "#0F172A",
    "input": "#1E293B",
    "border": "#334155",
    "green": "#22C55E",
    "red": "#F87171",
    "gold": "#F59E0B",
    "blue": "#60A5FA",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
}

_GRID = "#16233B"
_FONT = "'IBM Plex Sans',sans-serif"


def _rgba(hex6: str, alpha: float) -> str:
    """Convierte ``#RRGGBB`` + alpha (0–1) a ``rgba(r,g,b,a)`` para Plotly."""
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
    """Inyecta el CSS global de la app (fuentes, fondos, inputs, botones)."""
    st.markdown(
        f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    * {{font-family:{_FONT}!important}}
    #MainMenu,footer,header {{visibility:hidden}}
    .block-container {{padding-top:1.2rem;padding-bottom:3rem;max-width:1180px}}
    .stApp {{background:{C['bg']}}}
    h1,h2,h3,h4,p,span,label,div {{color:{C['text']}}}
    ::selection {{background:{C['green']}44}}
    ::-webkit-scrollbar {{width:10px;height:10px}}
    ::-webkit-scrollbar-track {{background:{C['bg']}}}
    ::-webkit-scrollbar-thumb {{background:{C['input']};border-radius:6px}}
    ::-webkit-scrollbar-thumb:hover {{background:{C['border']}}}

    .stTextInput input,.stNumberInput input,.stDateInput input,
    textarea,.stTextArea textarea {{
        background:{C['input']}!important;color:{C['text']}!important;
        border:1px solid {C['border']}!important;border-radius:8px!important;
        transition:border-color 150ms ease!important}}
    .stTextInput input:focus,.stNumberInput input:focus,
    .stTextArea textarea:focus {{
        border-color:{C['green']}!important;
        box-shadow:0 0 0 1px {C['green']}55!important}}
    div[data-baseweb="select"]>div {{
        background:{C['input']}!important;border:1px solid {C['border']}!important;
        border-radius:8px!important;color:{C['text']}!important}}

    .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button {{
        background:{C['green']}!important;color:#03130A!important;border:none!important;
        border-radius:8px!important;font-weight:600!important;padding:.5rem 1.2rem!important;
        cursor:pointer!important;transition:filter 180ms ease,box-shadow 180ms ease!important}}
    .stButton>button:hover,.stDownloadButton>button:hover,
    .stFormSubmitButton>button:hover {{
        filter:brightness(1.12)!important;
        box-shadow:0 4px 18px {C['green']}40!important}}
    .stButton>button:focus-visible,.stDownloadButton>button:focus-visible,
    .stFormSubmitButton>button:focus-visible {{
        outline:2px solid {C['text']}!important;outline-offset:2px!important}}

    .stSlider [data-baseweb="slider"] div[role="slider"] {{
        background:{C['green']}!important}}
    .stTabs [aria-selected="true"] {{
        color:{C['text']}!important;border-bottom:2px solid {C['green']}!important}}

    /* Sidebar: navegación tipo app moderna sobre st.radio */
    div[data-testid="stSidebar"] {{
        background:{C['card']}!important;border-right:1px solid {C['border']}!important}}
    div[data-testid="stSidebar"] .stRadio label {{
        display:flex!important;align-items:center;color:{C['muted']}!important;
        font-weight:500;padding:9px 12px!important;margin:2px 0!important;
        border-radius:8px!important;cursor:pointer!important;
        transition:background 150ms ease,color 150ms ease!important}}
    div[data-testid="stSidebar"] .stRadio label:hover {{
        background:{C['input']}55!important;color:{C['text']}!important}}
    div[data-testid="stSidebar"] .stRadio label:has(input:checked) {{
        background:{C['input']}!important;color:{C['text']}!important;
        box-shadow:inset 3px 0 0 {C['green']}!important}}
    div[data-testid="stSidebar"] .stRadio label:has(input:checked) p {{
        font-weight:600!important}}
    div[data-testid="stSidebar"] .stRadio label>div:first-child {{display:none!important}}

    div[data-testid="stExpander"] {{
        background:{C['card']}!important;border:1px solid {C['border']}!important;
        border-radius:10px!important}}
    .stDataFrame {{border:1px solid {C['border']}!important;border-radius:10px!important}}
    hr {{border-color:{C['border']}!important}}

    .fco-card {{transition:border-color 180ms ease,box-shadow 180ms ease}}
    .fco-card:hover {{border-color:{C['muted']}66!important;
        box-shadow:0 6px 22px rgba(2,6,23,.55)}}

    @media (prefers-reduced-motion: reduce) {{
        * {{transition:none!important;animation:none!important}}
    }}
    </style>""",
        unsafe_allow_html=True,
    )


# ── Componentes HTML ─────────────────────────────────────────────────────────
def card(label: str, valor: str, delta: str = "",
         color: str = COLORS["green"], bg: str = COLORS["card"]) -> str:
    """Tarjeta KPI: etiqueta, valor grande tabular y delta opcional."""
    d = (f"<span style='color:{color};font-size:12px;margin-top:4px;display:block'>"
         f"{delta}</span>") if delta else ""
    return (
        f"<div class='fco-card' style=\"background:{bg};border:1px solid "
        f"{COLORS['border']};border-radius:12px;padding:16px 20px;height:100%\">"
        f"<div style=\"color:{COLORS['muted']};font-size:11px;font-weight:600;"
        f"text-transform:uppercase;letter-spacing:.06em\">{label}</div>"
        f"<div style=\"color:{COLORS['text']};font-size:30px;font-weight:700;"
        f"font-variant-numeric:tabular-nums;margin:6px 0 2px\">{valor}</div>{d}</div>"
    )


def fila_cards(cards: list[str], gap: int = 12) -> str:
    """Envuelve varias tarjetas en una fila flex responsiva."""
    inner = "".join(f"<div style='flex:1;min-width:170px'>{c}</div>" for c in cards)
    return (f"<div style='display:flex;gap:{gap}px;flex-wrap:wrap;margin:6px 0'>"
            f"{inner}</div>")


def barra_h(label: str, valor: float, maximo: float,
            color: str = COLORS["blue"], detalle: str = "") -> str:
    """Barra horizontal de progreso con etiqueta y detalle a la derecha."""
    p = min(100, (valor / maximo) * 100) if maximo else 0
    return (
        f"<div style='margin:10px 0'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"color:{COLORS['muted']};font-size:12px;margin-bottom:5px'>"
        f"<span style='font-weight:500'>{label}</span><span>{detalle}</span></div>"
        f"<div style='background:{_GRID};border-radius:6px;height:8px;overflow:hidden'>"
        f"<div style='width:{p:.1f}%;background:linear-gradient(90deg,{color},{color}cc);"
        f"height:8px;border-radius:6px;transition:width 400ms ease'></div></div></div>"
    )


def badge(texto: str, color: str = COLORS["green"]) -> str:
    """Etiqueta tipo pill con color de acento."""
    return (
        f"<span style='background:{color}22;color:{color};border:1px solid {color}44;"
        f"border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600'>"
        f"{texto}</span>"
    )


def pill_estado(texto: str, tipo: str = "ok") -> str:
    """Pill de estado con punto de color (ok=verde, alerta=ámbar, error=rojo)."""
    color = {"ok": COLORS["green"], "alerta": COLORS["gold"],
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
    sub = (f"<div style='color:{COLORS['muted']};font-size:13px;margin-top:2px'>"
           f"{subtitulo}</div>") if subtitulo else ""
    return (f"<div style='margin:24px 0 14px'>"
            f"<div style='color:{COLORS['text']};font-size:18px;font-weight:700'>"
            f"{titulo}</div>{sub}</div>")


def titulo_pagina(icon: str, titulo: str, subtitulo: str = "") -> None:
    """Encabezado de página: icono SVG en chip + título + subtítulo."""
    sub = (f"<div style='color:{COLORS['muted']};font-size:14px;margin-top:3px'>"
           f"{subtitulo}</div>") if subtitulo else ""
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin:2px 0 6px'>"
        f"<div style='background:{COLORS['card']};border:1px solid "
        f"{COLORS['border']};border-radius:10px;padding:9px;display:flex'>"
        f"{icono(icon, 22, COLORS['green'])}</div>"
        f"<div><div style='font-size:26px;font-weight:700;letter-spacing:-.01em'>"
        f"{titulo}</div>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def md(html: str) -> None:
    """Atajo para renderizar HTML custom."""
    st.markdown(html, unsafe_allow_html=True)


# ── Gráficos Plotly (tema oscuro) ────────────────────────────────────────────
def _base_layout(fig: go.Figure, titulo: str = "", height: int = 350) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"])),
        margin=dict(l=0, r=70, t=40 if titulo else 10, b=0),
        height=height, font=dict(family="IBM Plex Sans", color=COLORS["muted"]),
        hoverlabel=dict(bgcolor=COLORS["input"], bordercolor=COLORS["border"],
                        font=dict(family="IBM Plex Sans", color=COLORS["text"])),
        showlegend=False,
    )
    return fig


def plotly_barras_h(labels, valores, titulo: str = "",
                    color: str = COLORS["blue"], fmt: str = "$,.0f",
                    resaltar_primero: bool = True) -> go.Figure:
    """Barras horizontales; resalta la primera (mejor opción) por defecto."""
    n = len(labels)
    colores = [color if (resaltar_primero and i == 0) else "#2D3B55"
               for i in range(n)]
    fig = go.Figure(go.Bar(
        x=list(valores), y=list(labels), orientation="h",
        marker=dict(color=colores, line=dict(width=0)),
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:{fmt}}}<extra></extra>",
        text=[f"{v:,.0f}" for v in valores], textposition="outside",
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


def plotly_area(x, y, titulo: str = "", color: str = COLORS["green"],
                fmt: str = "$,.0f", nombre: str = "") -> go.Figure:
    """Área acumulada (p. ej. ingreso neto anual mes a mes)."""
    fig = go.Figure(go.Scatter(
        x=list(x), y=list(y), mode="lines+markers",
        line=dict(color=color, width=2.5, shape="spline"),
        marker=dict(color=color, size=6),
        fill="tozeroy", fillcolor=_rgba(color, 0.13),
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
    colores = colores or [COLORS["green"], COLORS["red"],
                          COLORS["gold"], COLORS["blue"]]
    fig = go.Figure(go.Pie(
        labels=list(labels), values=list(valores), hole=0.62,
        marker=dict(colors=colores, line=dict(color=COLORS["bg"], width=2)),
        textinfo="percent", textfont=dict(family="IBM Plex Sans", size=12,
                                           color=COLORS["bg"]),
        hovertemplate="<b>%{label}</b><br>%{value:$,.0f} (%{percent})<extra></extra>",
    ))
    _base_layout(fig, titulo, height=320)
    fig.update_layout(margin=dict(l=0, r=0, t=40 if titulo else 10, b=0),
                      showlegend=True,
                      legend=dict(font=dict(color=COLORS["muted"], size=11),
                                  orientation="h", y=-0.05))
    return fig
