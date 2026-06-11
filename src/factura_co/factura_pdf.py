"""
factura_pdf.py — Generador de facturas profesionales en PDF.

A diferencia de :mod:`documento_pdf` (cuenta de cobro con estructura anidada),
este módulo expone una API plana y directa pensada para integrarse con
formularios web: recibe un único diccionario con los campos del documento y
devuelve los bytes del PDF, listos para `st.download_button` o para guardar
en disco.

Identidad visual (sistema ui-ux-pro-max · Glassmorphism fintech):
    - Cabecera de marca en azul slate profundo (#0F172A) con barra de acento
      dorado/violeta, chip de iniciales y bloque «FACTURA N.º …» destacado.
    - Tarjetas de cliente y resumen, tabla de conceptos con cabecera oscura
      y zebra striping, y bloque de total en caja oscura con cifra dorada.
    - Jerarquía tipográfica real (etiquetas pequeñas en mayúsculas con
      tracking, valores tabulares grandes) y espaciado generoso.

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

# ── Paleta de marca (Glassmorphism fintech: slate + oro + violeta) ───────────
_SLATE_900   = (15, 23, 42)      # #0F172A banda de marca y caja de total
_SLATE_700   = (51, 65, 85)      # #334155 texto secundario fuerte
_SLATE_500   = (100, 116, 139)   # #64748B etiquetas y texto auxiliar
_SLATE_200   = (226, 232, 240)   # #E2E8F0 bordes suaves
_SLATE_100   = (241, 245, 249)   # #F1F5F9 tarjetas de información
_SLATE_50    = (248, 250, 252)   # #F8FAFC filas zebra
_ORO         = (245, 158, 11)    # #F59E0B acento principal
_ORO_SUAVE   = (254, 243, 199)   # #FEF3C7 pill del número de documento
_VIOLETA     = (139, 92, 246)    # #8B5CF6 acento secundario de la barra
_ROJO        = (220, 38, 38)     # #DC2626 retenciones / descuentos
_VERDE       = (5, 150, 105)     # #059669 refuerzo positivo
_TINTA       = (15, 23, 42)      # texto principal (mismo slate 900)
_BLANCO      = (255, 255, 255)
_NUBE        = (203, 213, 225)   # #CBD5E1 texto claro sobre banda oscura

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

# Geometría base (A4 vertical, márgenes simétricos).
_MARGEN = 16
_ANCHO = 210
_CONTENIDO = _ANCHO - 2 * _MARGEN  # 178 mm útiles


def _fmt_cop(valor: float) -> str:
    """Formatea un número como pesos colombianos: ``$ 5.000.000``."""
    return "$ " + f"{valor:,.0f}".replace(",", ".")


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
    """Subclase FPDF con pie de página fiscal de marca."""

    def __init__(self):
        super().__init__()
        self.set_margins(_MARGEN, _MARGEN, _MARGEN)
        self.set_auto_page_break(auto=True, margin=24)

    def normalize_text(self, txt):
        """Sustituye caracteres fuera de latin-1 por equivalentes seguros."""
        reemplazos = {
            "—": "-", "–": "-",            # em/en dash
            "‘": "'", "’": "'",            # comillas simples
            "“": '"', "”": '"',            # comillas dobles
            "…": "...",                          # ellipsis
            " ": " ", " ": " ",            # espacios especiales
            "₱": "$",                            # símbolo peso variante
        }
        for orig, remp in reemplazos.items():
            txt = txt.replace(orig, remp)
        return super().normalize_text(txt)

    def footer(self):
        self.set_y(-18)
        # Barra de marca: segmento violeta + resto dorado, como en la cabecera.
        self.set_fill_color(*_VIOLETA)
        self.rect(_MARGEN, self.get_y(), 18, 0.9, style="F")
        self.set_fill_color(*_ORO)
        self.rect(_MARGEN + 18, self.get_y(), _CONTENIDO - 18, 0.9, style="F")
        self.ln(3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_SLATE_500)
        self.cell(
            0, 4,
            "Documento equivalente a factura - Art. 615 y 617 E.T. - "
            "Persona natural no responsable de IVA salvo indicación contraria.",
            align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.cell(0, 4, f"Página {self.page_no()}", align="C")
        self.set_text_color(*_TINTA)

    # ── Piezas visuales reutilizables ────────────────────────────────────────

    def etiqueta(self, texto: str, color=_SLATE_500):
        """Etiqueta pequeña en mayúsculas con tracking (jerarquía nivel 3)."""
        self.set_font("Helvetica", "B", 7)
        self.set_char_spacing(0.7)
        self.set_text_color(*color)
        self.cell(self.get_string_width(texto.upper()) + 4, 4, texto.upper(),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_char_spacing(0)
        self.set_text_color(*_TINTA)


def _iniciales(nombre: str) -> str:
    """Extrae hasta dos iniciales de un nombre para el logo placeholder."""
    partes = [p for p in nombre.split() if p]
    if not partes:
        return "FC"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[1][0]).upper()


def _cabecera_marca(pdf: _Factura, datos: dict, d: dict) -> None:
    """Banda superior de identidad: logo, emisor, contacto y «FACTURA N.º»."""
    pdf.set_fill_color(*_SLATE_900)
    pdf.rect(0, 0, _ANCHO, 42, style="F")
    # Barra de acento bicolor bajo la banda (violeta → dorado).
    pdf.set_fill_color(*_VIOLETA)
    pdf.rect(0, 42, 64, 1.8, style="F")
    pdf.set_fill_color(*_ORO)
    pdf.rect(64, 42, _ANCHO - 64, 1.8, style="F")

    # Chip de iniciales (logo placeholder) en dorado.
    pdf.set_fill_color(*_ORO)
    pdf.rect(_MARGEN, 10.5, 16.5, 16.5, style="F", round_corners=True,
             corner_radius=4)
    pdf.set_xy(_MARGEN, 10.5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*_SLATE_900)
    pdf.cell(16.5, 16.5, _iniciales(str(datos["nombre_freelancer"])), align="C")

    # Nombre del emisor + NIT + contacto, junto al chip.
    pdf.set_xy(37, 10)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(92, 8, str(datos["nombre_freelancer"])[:34],
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(37)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_ORO)
    pdf.cell(92, 5, f"NIT/CC {datos['nit_freelancer']}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    contacto = " · ".join(
        str(datos[k]) for k in ("ciudad", "email", "telefono") if datos.get(k)
    )
    if contacto:
        pdf.set_x(37)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*_NUBE)
        pdf.cell(92, 4.5, contacto[:64])

    # Bloque derecho: «FACTURA», pill con el número y fecha.
    pdf.set_xy(120, 9)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(74, 10, "FACTURA", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 9)
    num_txt = f"N.º {d['numero']}"
    w_pill = pdf.get_string_width(num_txt) + 8
    x_pill = _ANCHO - _MARGEN - w_pill
    pdf.set_fill_color(*_ORO)
    pdf.rect(x_pill, 21.5, w_pill, 7, style="F", round_corners=True,
             corner_radius=3)
    pdf.set_xy(x_pill, 21.5)
    pdf.set_text_color(*_SLATE_900)
    pdf.cell(w_pill, 7, num_txt, align="C")

    pdf.set_xy(120, 30.5)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_NUBE)
    pdf.cell(74, 5, f"Fecha de emisión: {d['fecha_str']}", align="R")

    pdf.set_text_color(*_TINTA)
    pdf.set_y(51)


def _tarjetas_info(pdf: _Factura, datos: dict, d: dict) -> None:
    """Tarjeta «Facturar a» (cliente) + tarjeta resumen del documento."""
    y0 = pdf.get_y()
    w_cli, w_res, gap = 106, 66, 6
    x_cli = _MARGEN
    x_res = _MARGEN + w_cli + gap

    cliente_lineas = [f"NIT {datos['nit_cliente']}"]
    if datos.get("ciudad_cliente"):
        cliente_lineas.append(str(datos["ciudad_cliente"]))
    # La razón social se envuelve (no se trunca): el nombre legal completo
    # importa. La altura de ambas tarjetas se calcula con el texto real.
    pdf.set_font("Helvetica", "B", 11)
    h_nombre = max(6.5, pdf.multi_cell(w_cli - 12, 6, str(datos["nombre_cliente"]),
                                       dry_run=True, output="HEIGHT"))
    h = max(30, 11 + h_nombre + 5 * len(cliente_lineas) + 5)

    # Tarjeta del cliente.
    pdf.set_fill_color(*_SLATE_100)
    pdf.rect(x_cli, y0, w_cli, h, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(x_cli + 6, y0 + 5)
    pdf.etiqueta("Facturar a", _ORO)
    pdf.set_x(x_cli + 6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(w_cli - 12, 6, str(datos["nombre_cliente"]),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_SLATE_700)
    for linea in cliente_lineas:
        pdf.set_x(x_cli + 6)
        pdf.cell(w_cli - 12, 5, linea, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_TINTA)

    # Tarjeta resumen: número, fecha y total, escaneable de un vistazo.
    pdf.set_fill_color(*_SLATE_100)
    pdf.rect(x_res, y0, w_res, h, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(x_res + 6, y0 + 5)
    pdf.etiqueta("Resumen", _SLATE_500)
    pdf.set_x(x_res + 6)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_SLATE_700)
    pdf.cell(24, 5, "Documento")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*_TINTA)
    pdf.cell(w_res - 36, 5, d["numero"][:18], align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(x_res + 6)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_SLATE_700)
    pdf.cell(24, 5, "Fecha")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*_TINTA)
    pdf.cell(w_res - 36, 5, d["fecha"].strftime("%d/%m/%Y"), align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(x_res + 6)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_SLATE_700)
    pdf.cell(24, 6, "Total")
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*_VERDE)
    pdf.cell(w_res - 36, 6, _fmt_cop(d["total"]), align="R")
    pdf.set_text_color(*_TINTA)

    pdf.set_y(y0 + h + 8)


def _tabla_conceptos(pdf: _Factura, d: dict) -> None:
    """Tabla de servicios: cabecera oscura, zebra y montos tabulares."""
    w_desc, w_val = 126, 52

    pdf.set_fill_color(*_SLATE_900)
    pdf.set_text_color(*_BLANCO)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_char_spacing(0.5)
    pdf.cell(w_desc, 9, "   DESCRIPCIÓN DEL SERVICIO", fill=True)
    pdf.cell(w_val, 9, "VALOR (COP)   ", align="R", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_char_spacing(0)
    pdf.set_text_color(*_TINTA)

    for i, (desc, valor) in enumerate(d["items"]):
        y_inicio = pdf.get_y()
        pdf.set_font("Helvetica", "", 9.5)
        # Altura real del texto envuelto, para pintar la zebra completa
        # y mantener la sangría en todas las líneas.
        alto_texto = pdf.multi_cell(w_desc - 10, 5.5, desc, dry_run=True,
                                    output="HEIGHT")
        alto = max(8.5, alto_texto + 3.5)
        if y_inicio + alto > pdf.page_break_trigger:
            pdf.add_page()
            y_inicio = pdf.get_y()
        if i % 2 == 0:
            pdf.set_fill_color(*_SLATE_50)
            pdf.rect(_MARGEN, y_inicio, w_desc + w_val, alto, style="F")
        pdf.set_xy(_MARGEN + 5, y_inicio + 1.75)
        pdf.multi_cell(w_desc - 10, 5.5, desc,
                       new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_xy(_MARGEN + w_desc, y_inicio)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(w_val - 5, alto, _fmt_cop(valor), align="R")
        pdf.set_y(y_inicio + alto)

    # Cierre de tabla con la línea de acento dorada.
    pdf.set_draw_color(*_ORO)
    pdf.set_line_width(0.5)
    pdf.line(_MARGEN, pdf.get_y(), _ANCHO - _MARGEN, pdf.get_y())
    pdf.ln(5)


def _bloque_totales(pdf: _Factura, d: dict) -> float:
    """Subtotal, retención y caja oscura de TOTAL. Devuelve la Y final."""
    x_tot = 108
    w_tot = _ANCHO - _MARGEN - x_tot  # 86 mm
    w_etq, w_val = 46, w_tot - 46

    pdf.set_xy(x_tot, pdf.get_y())
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_SLATE_700)
    pdf.cell(w_etq, 6.5, "Subtotal", align="R")
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*_TINTA)
    pdf.cell(w_val, 6.5, _fmt_cop(d["subtotal"]) + "  ", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if d["retencion_valor"] > 0:
        pdf.set_x(x_tot)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*_SLATE_700)
        pdf.cell(w_etq, 6.5, f"Retención fuente ({d['retencion_pct'] * 100:.0f}%)",
                 align="R")
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*_ROJO)
        pdf.cell(w_val, 6.5, "- " + _fmt_cop(d["retencion_valor"]) + "  ",
                 align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TINTA)

    # Caja de TOTAL A PAGAR: slate profundo con la cifra en dorado.
    pdf.ln(2)
    y_caja = pdf.get_y()
    pdf.set_fill_color(*_SLATE_900)
    pdf.rect(x_tot, y_caja, w_tot, 14, style="F", round_corners=True,
             corner_radius=3)
    pdf.set_xy(x_tot + 5, y_caja)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_char_spacing(0.5)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(40, 14, "TOTAL A PAGAR")
    pdf.set_char_spacing(0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*_ORO)
    pdf.set_xy(x_tot, y_caja)
    pdf.cell(w_tot - 5, 14, _fmt_cop(d["total"]), align="R")
    pdf.set_text_color(*_TINTA)
    return y_caja + 14


def _bloque_pago(pdf: _Factura, datos: dict, y0: float) -> float:
    """«Datos para el pago» a la izquierda de los totales. Devuelve Y final."""
    if not (datos.get("forma_de_pago") or datos.get("banco")):
        return y0

    x_pago, w_pago = _MARGEN, 86
    pdf.set_xy(x_pago, y0)
    pdf.etiqueta("Datos para el pago", _ORO)

    pdf.set_font("Helvetica", "", 8.5)
    if datos.get("forma_de_pago"):
        pdf.set_x(x_pago)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(26, 5, "Forma de pago:")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(w_pago - 26, 5, str(datos["forma_de_pago"]),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if datos.get("banco"):
        tipo = datos.get("tipo_cuenta", "Ahorros")
        cuenta = datos.get("cuenta", "")
        pdf.set_x(x_pago)
        pdf.set_text_color(*_SLATE_700)
        pdf.multi_cell(
            w_pago, 5,
            f"{datos['banco']} · {tipo} N.º {cuenta}\n"
            f"Titular: {datos['nombre_freelancer']} ({datos['nit_freelancer']})",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_text_color(*_TINTA)
    return pdf.get_y()


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
                - ``forma_de_pago`` (str): medio de pago acordado
                  (transferencia, Nequi, etc.). Se renderiza en una línea
                  dedicada dentro de «Datos para el pago», no dentro de notas.
                - ``banco`` (str), ``cuenta`` (str), ``tipo_cuenta`` (str):
                  instrucciones de pago.
                - ``notas`` (str): texto libre al pie (vigencia, condiciones).

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

    _cabecera_marca(pdf, datos, d)
    _tarjetas_info(pdf, datos, d)
    _tabla_conceptos(pdf, d)

    y_detalle = pdf.get_y()
    y_fin_totales = _bloque_totales(pdf, d)
    y_fin_pago = _bloque_pago(pdf, datos, y_detalle)
    pdf.set_y(max(y_fin_totales, y_fin_pago) + 8)

    # Notas / condiciones a ancho completo, bajo ambos bloques.
    if datos.get("notas"):
        pdf.etiqueta("Condiciones", _SLATE_500)
        pdf.set_font("Helvetica", "I", 8.5)
        pdf.set_text_color(*_SLATE_500)
        pdf.multi_cell(_CONTENIDO, 5, str(datos["notas"]),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TINTA)

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
