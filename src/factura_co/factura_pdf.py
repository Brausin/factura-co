"""
factura_pdf.py — Generador de facturas/cuentas profesionales en PDF.

A diferencia de :mod:`documento_pdf` (cuenta de cobro con estructura anidada),
este módulo expone una API plana y directa pensada para integrarse con
formularios web: recibe un único diccionario con los campos del documento y
devuelve los bytes del PDF, listos para `st.download_button` o para guardar
en disco.

El documento generado tiene identidad de marca (banda superior oscura con
acentos dorado/verde) pero conserva un cuerpo claro, imprimible y legible en
blanco y negro.

Marco legal:
    - Artículo 615 ET: obligación de expedir factura o documento equivalente.
    - Artículo 617 ET: requisitos de la factura de venta.
    - Artículo 392 ET: retención en la fuente por honorarios y servicios.

Dependencia:
    pip install fpdf2

Uso básico:
    from factura_co.factura_pdf import generar_factura

    pdf_bytes = generar_factura({
        "nombre_freelancer": "Ana García",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": "Desarrollo de API de pagos — Sprint 3",
        "valor_cop": 5_000_000,
        "retencion_pct": 11,
        "numero_factura": "FV-2026-014",
    })
    with open("factura.pdf", "wb") as f:
        f.write(pdf_bytes)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

try:
    from fpdf import FPDF, XPos, YPos
except ImportError:
    raise ImportError(
        "fpdf2 es requerido para generar PDFs. Instálalo con: pip install fpdf2"
    )

# ── Paleta de marca (factura-co dark finance) ────────────────────────────────
_FONDO_OSCURO = (13, 17, 23)     # #0D1117 banda superior
_CARD_OSCURO  = (33, 38, 45)     # #21262D cabecera de tabla
_DORADO       = (245, 166, 35)   # #F5A623 acento principal
_VERDE        = (0, 160, 120)    # #00A078 neto a favor (versión imprimible)
_ROJO         = (198, 40, 55)    # retenciones / descuentos
_NEGRO        = (28, 33, 40)     # texto principal
_GRIS_TEXTO   = (110, 118, 128)  # texto secundario
_GRIS_CLARO   = (244, 246, 248)  # filas alternas
_GRIS_BORDE   = (210, 215, 222)  # bordes suaves
_BLANCO       = (255, 255, 255)

_MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# Campos obligatorios del diccionario de entrada.
_REQUERIDOS = (
    "nombre_freelancer",
    "nit_freelancer",
    "nombre_cliente",
    "nit_cliente",
    "descripcion_servicio",
    "valor_cop",
)


def _fmt_cop(valor: float) -> str:
    """Formatea un número como pesos colombianos: ``$ 5.000.000``."""
    return f"$ {valor:,.0f}"


def _parse_fecha(valor: Union[None, str, date, datetime]) -> date:
    """Normaliza el campo ``fecha`` a un objeto :class:`date`.

    Acepta ``None`` (hoy), una fecha ISO ``YYYY-MM-DD``, o un objeto
    ``date``/``datetime``.
    """
    if valor is None:
        return date.today()
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        texto = valor.strip()
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            # Acepta también DD/MM/YYYY, formato común en formularios locales.
            return datetime.strptime(texto, "%d/%m/%Y").date()
    raise ValueError(f"Formato de fecha no soportado: {valor!r}")


def _fecha_larga(f: date) -> str:
    """Convierte una fecha a texto legible: ``7 de junio de 2026``."""
    return f"{f.day} de {_MESES_ES[f.month]} de {f.year}"


def _normalizar_pct(valor: Union[int, float]) -> float:
    """Devuelve la retención como fracción (0–1).

    Acepta tanto porcentaje (``11`` → 0.11) como fracción (``0.11`` → 0.11).
    Cualquier valor mayor a 1 se interpreta como porcentaje.
    """
    valor = float(valor)
    if valor < 0:
        raise ValueError("retencion_pct no puede ser negativa")
    return valor / 100.0 if valor > 1 else valor


def _desglose_factura(datos: dict) -> dict:
    """Valida la entrada y calcula el desglose económico de la factura.

    Esta función es pura (no genera PDF) para poder probarse de forma
    aislada. Devuelve un diccionario con todos los valores ya calculados y
    normalizados que :func:`generar_factura` usa para renderizar.

    Args:
        datos: Diccionario con los campos de la factura. Ver :func:`generar_factura`.

    Returns:
        dict con: ``numero``, ``fecha`` (date), ``fecha_str``, ``items``
        (lista de ``(descripcion, valor)``), ``subtotal``, ``retencion_pct``
        (fracción), ``retencion_valor``, ``total``.

    Raises:
        ValueError: si falta un campo obligatorio o si ``valor_cop`` es inválido.
    """
    faltantes = [c for c in _REQUERIDOS if c not in datos or datos[c] in (None, "")]
    if faltantes:
        raise ValueError(
            "Faltan campos obligatorios en la factura: " + ", ".join(faltantes)
        )

    # Items: permite varias líneas vía datos["items"] = [(desc, valor), ...];
    # si no, una sola línea a partir de descripcion_servicio + valor_cop.
    items = datos.get("items")
    if items:
        items = [(str(d), float(v)) for d, v in items]
    else:
        try:
            valor = float(datos["valor_cop"])
        except (TypeError, ValueError):
            raise ValueError("valor_cop debe ser numérico")
        if valor <= 0:
            raise ValueError("valor_cop debe ser mayor que cero")
        items = [(str(datos["descripcion_servicio"]), valor)]

    subtotal = round(sum(v for _, v in items))
    retencion_pct = _normalizar_pct(datos.get("retencion_pct", 0))
    retencion_valor = round(subtotal * retencion_pct)
    total = subtotal - retencion_valor

    fecha = _parse_fecha(datos.get("fecha"))
    numero = str(
        datos.get("numero_factura")
        or f"FV-{fecha.strftime('%Y%m%d')}"
    )

    return {
        "numero": numero,
        "fecha": fecha,
        "fecha_str": _fecha_larga(fecha),
        "items": items,
        "subtotal": subtotal,
        "retencion_pct": retencion_pct,
        "retencion_valor": retencion_valor,
        "total": total,
    }


class _Factura(FPDF):
    """Subclase FPDF con banda de marca y pie de página fiscal."""

    def __init__(self):
        super().__init__()
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=20)

    def normalize_text(self, txt):
        """Sustituye caracteres fuera de latin-1 por equivalentes seguros."""
        reemplazos = {
            "—": "-", "–": "-",            # em/en dash
            "‘": "'", "’": "'",            # comillas simples
            "“": '"', "”": '"',            # comillas dobles
            "…": "...", "·": ".",          # ellipsis / punto medio
            " ": " ", " ": " ",            # espacios especiales
            "₱": "$",                            # símbolo peso variante
        }
        for orig, remp in reemplazos.items():
            txt = txt.replace(orig, remp)
        return super().normalize_text(txt)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*_GRIS_BORDE)
        self.set_line_width(0.3)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(1.5)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_GRIS_TEXTO)
        self.cell(
            0, 5,
            "Documento equivalente a factura - Art. 615 y 617 E.T. - "
            "Persona natural no responsable de IVA salvo indicacion contraria.",
            align="C",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.cell(
            0, 4,
            f"Pagina {self.page_no()}",
            align="C",
        )
        self.set_text_color(*_NEGRO)


def _iniciales(nombre: str) -> str:
    """Extrae hasta dos iniciales de un nombre para el logo placeholder."""
    partes = [p for p in nombre.split() if p]
    if not partes:
        return "FC"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def generar_factura(datos: dict) -> bytes:
    """Genera una factura profesional en PDF a partir de un diccionario plano.

    Args:
        datos: Diccionario con los campos del documento.

            Obligatorios:
                - ``nombre_freelancer`` (str): razón social / nombre del emisor.
                - ``nit_freelancer`` (str): NIT o cédula del emisor.
                - ``nombre_cliente`` (str): razón social del cliente.
                - ``nit_cliente`` (str): NIT del cliente.
                - ``descripcion_servicio`` (str): detalle del servicio prestado.
                - ``valor_cop`` (number): valor bruto en pesos.

            Opcionales:
                - ``retencion_pct`` (number): retención en la fuente. Acepta
                  porcentaje (``11``) o fracción (``0.11``). Default 0.
                - ``fecha`` (date | str): fecha del documento. Default hoy.
                - ``numero_factura`` (str): consecutivo. Default generado.
                - ``items`` (list[tuple[str, number]]): varias líneas de
                  servicio; si se provee, sustituye a ``descripcion_servicio``
                  y ``valor_cop`` para el detalle.
                - ``ciudad`` (str), ``email`` (str), ``telefono`` (str):
                  datos de contacto del emisor.
                - ``banco`` (str), ``cuenta`` (str), ``tipo_cuenta`` (str):
                  instrucciones de pago.
                - ``notas`` (str): texto libre al pie (forma de pago, vigencia).

    Returns:
        bytes: contenido del PDF, listo para descargar o guardar.

    Raises:
        ValueError: si falta algún campo obligatorio o ``valor_cop`` es inválido.

    Examples:
        >>> pdf = generar_factura({
        ...     "nombre_freelancer": "Ana García",
        ...     "nit_freelancer": "52.123.456-7",
        ...     "nombre_cliente": "Tech Corp SAS",
        ...     "nit_cliente": "900.123.456-7",
        ...     "descripcion_servicio": "Consultoría Sprint 3",
        ...     "valor_cop": 3_000_000,
        ...     "retencion_pct": 11,
        ... })
        >>> pdf[:4] == b"%PDF"
        True
    """
    d = _desglose_factura(datos)

    pdf = _Factura()
    pdf.add_page()

    # ── BANDA SUPERIOR DE MARCA ──────────────────────────────────────────────
    pdf.set_fill_color(*_FONDO_OSCURO)
    pdf.rect(0, 0, 210, 34, style="F")

    # Logo placeholder: cuadro dorado con iniciales del emisor.
    pdf.set_fill_color(*_DORADO)
    pdf.rect(18, 9, 16, 16, style="F")
    pdf.set_xy(18, 9)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*_FONDO_OSCURO)
    pdf.cell(16, 16, _iniciales(str(datos["nombre_freelancer"])), align="C")

    # Nombre del emisor junto al logo.
    pdf.set_xy(38, 11)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(110, 7, str(datos["nombre_freelancer"])[:38],
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(38)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_DORADO)
    pdf.cell(110, 5, f"NIT/CC: {datos['nit_freelancer']}")

    # Bloque "FACTURA" alineado a la derecha de la banda.
    pdf.set_xy(120, 9)
    pdf.set_font("Helvetica", "B", 19)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(72, 9, "FACTURA", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(120)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_GRIS_BORDE)
    pdf.cell(72, 5, f"N.o  {d['numero']}", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(120)
    pdf.cell(72, 5, f"Fecha:  {d['fecha_str']}", align="R")

    pdf.set_text_color(*_NEGRO)
    pdf.set_y(42)

    # ── PARTES (EMISOR / CLIENTE) ────────────────────────────────────────────
    y0 = pdf.get_y()
    col_w = 84
    gap = 6

    def _bloque_parte(x: float, titulo: str, color_titulo, lineas: list):
        pdf.set_xy(x, y0)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*color_titulo)
        pdf.cell(col_w, 5, titulo.upper(), new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_text_color(*_NEGRO)
        for i, (etq, val) in enumerate(lineas):
            pdf.set_x(x)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(20, 5.5, etq)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(col_w - 20, 5.5, str(val),
                           new_x=XPos.LEFT, new_y=YPos.NEXT)

    emisor_lineas = [("Nombre:", str(datos["nombre_freelancer"])),
                     ("NIT/CC:", str(datos["nit_freelancer"]))]
    if datos.get("ciudad"):
        emisor_lineas.append(("Ciudad:", str(datos["ciudad"])))
    if datos.get("email"):
        emisor_lineas.append(("Email:", str(datos["email"])))
    if datos.get("telefono"):
        emisor_lineas.append(("Tel:", str(datos["telefono"])))

    cliente_lineas = [("Razon:", str(datos["nombre_cliente"])),
                      ("NIT:", str(datos["nit_cliente"]))]
    if datos.get("ciudad_cliente"):
        cliente_lineas.append(("Ciudad:", str(datos["ciudad_cliente"])))

    _bloque_parte(18, "Emisor", _VERDE, emisor_lineas)
    y_emisor_fin = pdf.get_y()
    _bloque_parte(18 + col_w + gap, "Facturar a", _DORADO, cliente_lineas)
    y_cliente_fin = pdf.get_y()

    pdf.set_y(max(y_emisor_fin, y_cliente_fin) + 4)

    # ── TABLA DE SERVICIOS ───────────────────────────────────────────────────
    pdf.set_fill_color(*_CARD_OSCURO)
    pdf.set_text_color(*_BLANCO)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(126, 8, "  DESCRIPCION DEL SERVICIO", fill=True)
    pdf.cell(48, 8, "VALOR (COP)  ", align="R", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_NEGRO)

    for i, (desc, valor) in enumerate(d["items"]):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*_GRIS_CLARO)
        y_inicio = pdf.get_y()
        pdf.set_font("Helvetica", "", 9)
        # multi_cell para descripciones largas; el valor se alinea arriba.
        x_inicio = pdf.get_x()
        pdf.multi_cell(126, 7, "  " + desc, fill=fill,
                       new_x=XPos.RIGHT, new_y=YPos.TOP,
                       max_line_height=5.5)
        y_fin = pdf.get_y()
        alto = max(7, y_fin - y_inicio)
        pdf.set_xy(x_inicio + 126, y_inicio)
        pdf.cell(48, alto, _fmt_cop(valor) + "  ", align="R", fill=fill,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Línea de cierre de tabla.
    pdf.set_draw_color(*_GRIS_BORDE)
    pdf.set_line_width(0.3)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(3)

    # ── TOTALES (alineados a la derecha) ─────────────────────────────────────
    x_tot = 110
    w_etq, w_val = 50, 32

    def _fila_total(etq: str, val_str: str, color=None, negrita=False, fondo=None):
        pdf.set_x(x_tot)
        if fondo:
            pdf.set_fill_color(*fondo)
        pdf.set_font("Helvetica", "B" if negrita else "", 9.5 if negrita else 9)
        pdf.cell(w_etq, 8 if negrita else 6.5, etq, align="R", fill=bool(fondo))
        if color:
            pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B" if negrita else "", 10.5 if negrita else 9)
        pdf.cell(w_val, 8 if negrita else 6.5, val_str + " ", align="R",
                 fill=bool(fondo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_NEGRO)

    _fila_total("Subtotal:", _fmt_cop(d["subtotal"]))
    if d["retencion_valor"] > 0:
        pct_txt = f"Retencion fuente ({d['retencion_pct'] * 100:.0f}%):"
        _fila_total(pct_txt, "- " + _fmt_cop(d["retencion_valor"]), color=_ROJO)

    pdf.ln(0.5)
    _fila_total("TOTAL A PAGAR:", _fmt_cop(d["total"]),
                color=_VERDE, negrita=True, fondo=(232, 246, 241))

    # ── DATOS DE PAGO / NOTAS ────────────────────────────────────────────────
    if datos.get("banco") or datos.get("notas"):
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*_VERDE)
        pdf.cell(0, 5, "DATOS PARA EL PAGO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_NEGRO)
        pdf.set_font("Helvetica", "", 9)
        if datos.get("banco"):
            tipo = datos.get("tipo_cuenta", "Ahorros")
            cuenta = datos.get("cuenta", "")
            pdf.multi_cell(
                0, 5.5,
                f"{datos['banco']} - {tipo} N.o {cuenta}\n"
                f"Titular: {datos['nombre_freelancer']} ({datos['nit_freelancer']})",
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
        if datos.get("notas"):
            pdf.ln(1)
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(*_GRIS_TEXTO)
            pdf.multi_cell(0, 5, str(datos["notas"]),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*_NEGRO)

    return bytes(pdf.output())


def guardar_factura(contenido: bytes, ruta: str) -> str:
    """Guarda en disco los bytes de una factura generada.

    Args:
        contenido: bytes resultado de :func:`generar_factura`.
        ruta: ruta de destino del archivo ``.pdf``.

    Returns:
        La ruta del archivo guardado.
    """
    with open(ruta, "wb") as f:
        f.write(contenido)
    return ruta
