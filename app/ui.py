"""
ui.py — Sistema de diseño "dark finance" para la app de factura-co.

Centraliza la paleta, el CSS global y los componentes visuales reutilizables
(tarjetas, barras, badges, secciones) y los gráficos Plotly con tema oscuro.
La app (`app/main.py`) importa de aquí para mantener una estética coherente y
sin dependencias de los widgets por defecto de Streamlit que rompen el tema.

Reglas de diseño:
    - Nunca usar st.metric / st.bar_chart / matplotlib.
    - Todo número tabular con `font-variant-numeric: tabular-nums`.
    - Gráficos sin fondo (transparentes), grid sutil, hover informativo.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

# ── Paleta de marca ──────────────────────────────────────────────────────────
COLORS = {
    "bg": "#0D1117",
    "card": "#161B22",
    "input": "#21262D",
    "border": "#30363D",
    "green": "#00C896",
    "red": "#FF4B5C",
    "gold": "#F5A623",
    "blue": "#58A6FF",
    "text": "#E6EDF3",
    "muted": "#8B949E",
}

_GRID = "#1E2530"


def _rgba(hex6: str, alpha: float) -> str:
    """Convierte ``#RRGGBB`` + alpha (0–1) a ``rgba(r,g,b,a)`` para Plotly."""
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * {{font-family:'Inter',sans-serif!important}}
    #MainMenu,footer,header {{visibility:hidden}}
    .block-container {{padding-top:1.2rem;padding-bottom:3rem;max-width:1180px}}
    .stApp {{background:{C['bg']}}}
    h1,h2,h3,h4,p,span,label,div {{color:{C['text']}}}
    .stTextInput input,.stNumberInput input,.stDateInput input,
    textarea,.stTextArea textarea {{
        background:{C['input']}!important;color:{C['text']}!important;
        border:1px solid {C['border']}!important;border-radius:8px!important}}
    div[data-baseweb="select"]>div {{
        background:{C['input']}!important;border:1px solid {C['border']}!important;
        border-radius:8px!important;color:{C['text']}!important}}
    .stButton>button,.stDownloadButton>button {{
        background:{C['gold']}!important;color:#000!important;border:none!important;
        border-radius:8px!important;font-weight:600!important;padding:.5rem 1.1rem!important;
        transition:all 150ms ease!important}}
    .stButton>button:hover,.stDownloadButton>button:hover {{
        transform:translateY(-1px)!important;box-shadow:0 4px 14px rgba(245,166,35,.25)!important}}
    .stSlider [data-baseweb="slider"] div[role="slider"] {{background:{C['gold']}!important}}
    .stTabs [aria-selected="true"] {{
        color:{C['text']}!important;border-bottom:2px solid {C['gold']}!important}}
    div[data-testid="stSidebar"] {{
        background:{C['card']}!important;border-right:1px solid {C['border']}!important}}
    div[data-testid="stSidebar"] .stRadio label {{
        color:{C['text']}!important;font-weight:500;padding:2px 0}}
    div[data-testid="stExpander"] {{
        background:{C['card']}!important;border:1px solid {C['border']}!important;
        border-radius:10px!important}}
    .stDataFrame {{border:1px solid {C['border']}!important;border-radius:10px!important}}
    hr {{border-color:{C['border']}!important}}
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
        f"<div style=\"background:{bg};border:1px solid {COLORS['border']};"
        f"border-radius:12px;padding:16px 20px;height:100%\">"
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


def seccion(titulo: str, subtitulo: str = "") -> str:
    """Encabezado de sección con título y subtítulo opcional."""
    sub = (f"<div style='color:{COLORS['muted']};font-size:13px;margin-top:2px'>"
           f"{subtitulo}</div>") if subtitulo else ""
    return (f"<div style='margin:24px 0 14px'>"
            f"<div style='color:{COLORS['text']};font-size:18px;font-weight:700'>"
            f"{titulo}</div>{sub}</div>")


def md(html: str) -> None:
    """Atajo para renderizar HTML custom."""
    st.markdown(html, unsafe_allow_html=True)


# ── Gráficos Plotly (tema oscuro) ────────────────────────────────────────────
def _base_layout(fig: go.Figure, titulo: str = "", height: int = 350) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"])),
        margin=dict(l=0, r=70, t=40 if titulo else 10, b=0),
        height=height, font=dict(family="Inter", color=COLORS["muted"]),
        hoverlabel=dict(bgcolor=COLORS["input"], bordercolor=COLORS["border"],
                        font=dict(family="Inter", color=COLORS["text"])),
        showlegend=False,
    )
    return fig


def plotly_barras_h(labels, valores, titulo: str = "",
                    color: str = COLORS["blue"], fmt: str = "$,.0f",
                    resaltar_primero: bool = True) -> go.Figure:
    """Barras horizontales; resalta la primera (mejor opción) por defecto."""
    n = len(labels)
    colores = [color if (resaltar_primero and i == 0) else "#2D3748"
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
        textinfo="percent", textfont=dict(family="Inter", size=12,
                                           color=COLORS["bg"]),
        hovertemplate="<b>%{label}</b><br>%{value:$,.0f} (%{percent})<extra></extra>",
    ))
    _base_layout(fig, titulo, height=320)
    fig.update_layout(margin=dict(l=0, r=0, t=40 if titulo else 10, b=0),
                      showlegend=True,
                      legend=dict(font=dict(color=COLORS["muted"], size=11),
                                  orientation="h", y=-0.05))
    return fig
