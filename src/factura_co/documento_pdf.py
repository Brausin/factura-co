"""
documento_pdf.py — Generador de cuentas de cobro profesionales en PDF.

Produce documentos PDF listos para imprimir o enviar por correo, con la
identidad de marca de factura-co (sistema ui-ux-pro-max · Glassmorphism
fintech: slate profundo #0F172A + acento dorado #F59E0B) y toda la
información requerida por la regulación colombiana para personas naturales
no responsables de IVA.

Estructura visual:
    - Banda de marca con «CUENTA DE COBRO», número en pill dorado y fecha.
    - Tarjetas lado a lado «Cobrado por» / «Cobrado a».
    - Descripción del servicio en tarjeta clara.
    - Desglose de valores con cabecera oscura, zebra y retenciones en rojo.
    - Caja de NETO A PAGAR en slate con cifra dorada, imposible de ignorar.
    - Aportes SGSS (informativos), datos bancarios y firmas.

Marco legal:
    - Artículo 615 ET: Obligación de expedir factura o documento equivalente
    - Resolución DIAN 000042 de 2020: documentos equivalentes para
      personas naturales no obligadas a facturar electrónicamente
    - Conceptos DIAN sobre cuentas de cobro para independientes

Dependencia:
    pip install fpdf2

Uso básico:
    from factura_co.documento_pdf import generar_pdf

    pdf_bytes = generar_pdf(
        datos_freelancer={...},
        datos_cliente={...},
        valor=5_000_000,
        descripcion="Consultoría en transformación digital",
    )
    with open("cuenta_cobro.pdf", "wb") as f:
        f.write(pdf_bytes)
"""

from datetime import date
from typing import Optional

try:
    from fpdf import FPDF, XPos, YPos
    _FPDF2 = True
except ImportError:
    raise ImportError(
        "fpdf2 es requerido para generar PDFs. Instálalo con: pip install fpdf2"
    )

# ── Paleta de marca (Glassmorphism fintech: slate + oro) ─────────────────────
_SLATE_900  = (15, 23, 42)      # #0F172A banda y caja de neto
_SLATE_700  = (51, 65, 85)      # #334155 texto secundario fuerte
_SLATE_500  = (100, 116, 139)   # #64748B etiquetas / auxiliar
_SLATE_200  = (226, 232, 240)   # #E2E8F0 bordes suaves
_SLATE_100  = (241, 245, 249)   # #F1F5F9 tarjetas
_SLATE_50   = (248, 250, 252)   # #F8FAFC zebra
_ORO        = (245, 158, 11)    # #F59E0B acento principal
_VIOLETA    = (139, 92, 246)    # #8B5CF6 acento secundario
_ROJO       = (220, 38, 38)     # #DC2626 retenciones
_VERDE      = (5, 150, 105)     # #059669 refuerzo positivo
_TINTA      = (15, 23, 42)      # texto principal
_BLANCO     = (255, 255, 255)
_NUBE       = (203, 213, 225)   # texto claro sobre banda oscura

_MARGEN = 16
_ANCHO = 210
_CONTENIDO = _ANCHO - 2 * _MARGEN


def _normalizar_texto(texto: str) -> str:
    """Reemplaza caracteres fuera de latin-1 por equivalentes seguros."""
    reemplazos = {
        "—": "-",   # em dash
        "–": "-",   # en dash
        "‘": "'",   # comilla simple izquierda
        "’": "'",   # comilla simple derecha
        "“": '"',   # comilla doble izquierda
        "”": '"',   # comilla doble derecha
        "…": "...", # ellipsis
        " ": " ",   # espacio non-breaking
    }
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto


class _CuentaCobro(FPDF):
    """Subclase FPDF con cabecera de marca y pie de página."""

    def __init__(self, numero_doc: str, fecha_doc: str):
        super().__init__()
        self.numero_doc = numero_doc
        self.fecha_doc = fecha_doc
        self.set_margins(_MARGEN, _MARGEN, _MARGEN)
        self.set_auto_page_break(auto=True, margin=24)

    def normalize_text(self, txt):
        """Normaliza caracteres especiales a latin-1 seguro."""
        reemplazos = {
            "—": "-",   # em dash
            "–": "-",   # en dash
            "‘": "'",   # comilla izq
            "’": "'",   # comilla der
            "“": '"',   # doble izq
            "”": '"',   # doble der
            "…": "...", # ellipsis
            " ": " ",   # non-breaking space
        }
        for orig, remp in reemplazos.items():
            txt = txt.replace(orig, remp)
        return super().normalize_text(txt)

    def header(self):
        if self.page_no() == 1:
            # Banda principal de marca, solo en la primera página.
            self.set_fill_color(*_SLATE_900)
            self.rect(0, 0, _ANCHO, 36, style="F")
            self.set_fill_color(*_VIOLETA)
            self.rect(0, 36, 64, 1.8, style="F")
            self.set_fill_color(*_ORO)
            self.rect(64, 36, _ANCHO - 64, 1.8, style="F")

            self.set_xy(_MARGEN, 10)
            self.set_font("Helvetica", "B", 19)
            self.set_text_color(*_BLANCO)
            self.cell(110, 9, "CUENTA DE COBRO",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(_MARGEN)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*_NUBE)
            self.cell(110, 5, "Documento equivalente · Resolución DIAN 000042 de 2020")

            # Pill dorado con el número del documento.
            self.set_font("Helvetica", "B", 9)
            num_txt = f"N.º {self.numero_doc}"
            w_pill = self.get_string_width(num_txt) + 8
            x_pill = _ANCHO - _MARGEN - w_pill
            self.set_fill_color(*_ORO)
            self.rect(x_pill, 10, w_pill, 7, style="F", round_corners=True,
                      corner_radius=3)
            self.set_xy(x_pill, 10)
            self.set_text_color(*_SLATE_900)
            self.cell(w_pill, 7, num_txt, align="C")

            self.set_xy(110, 19.5)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*_NUBE)
            self.cell(84, 5, f"Fecha: {self.fecha_doc}", align="R")

            self.set_text_color(*_TINTA)
            self.set_y(45)
        else:
            # Páginas siguientes: banda delgada con la referencia del documento.
            self.set_fill_color(*_SLATE_900)
            self.rect(0, 0, _ANCHO, 12, style="F")
            self.set_xy(_MARGEN, 2.5)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*_BLANCO)
            self.cell(100, 7, f"CUENTA DE COBRO · N.º {self.numero_doc}")
            self.set_xy(110, 2.5)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*_NUBE)
            self.cell(84, 7, self.fecha_doc, align="R")
            self.set_text_color(*_TINTA)
            self.set_y(18)

    def footer(self):
        self.set_y(-18)
        self.set_fill_color(*_VIOLETA)
        self.rect(_MARGEN, self.get_y(), 18, 0.9, style="F")
        self.set_fill_color(*_ORO)
        self.rect(_MARGEN + 18, self.get_y(), _CONTENIDO - 18, 0.9, style="F")
        self.ln(3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*_SLATE_500)
        self.cell(0, 4,
                  "Documento generado con factura-co · github.com/Brausin/factura-co",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 4, f"Página {self.page_no()}", align="C")
        self.set_text_color(*_TINTA)

    # ── Bloques reutilizables ─────────────────────────────────────────────────

    def etiqueta(self, texto: str, color=_ORO):
        """Etiqueta pequeña en mayúsculas con tracking."""
        self.set_font("Helvetica", "B", 7)
        self.set_char_spacing(0.7)
        self.set_text_color(*color)
        self.cell(self.get_string_width(texto.upper()) + 4, 4, texto.upper(),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_char_spacing(0)
        self.set_text_color(*_TINTA)

    def titulo_seccion(self, texto: str):
        """Encabezado de sección: etiqueta dorada + línea suave."""
        self.ln(5)
        self.etiqueta(texto, _ORO)
        self.set_draw_color(*_SLATE_200)
        self.set_line_width(0.3)
        self.line(_MARGEN, self.get_y(), _ANCHO - _MARGEN, self.get_y())
        self.ln(2.5)

    def fila_dato(self, etiqueta: str, valor: str, bg_gris: bool = False):
        """Fila etiqueta–valor dentro de una sección."""
        fill = bool(bg_gris)
        if fill:
            self.set_fill_color(*_SLATE_50)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_SLATE_500)
        self.cell(46, 6.5, "  " + etiqueta, fill=fill)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_TINTA)
        self.cell(0, 6.5, str(valor), new_x=XPos.LMARGIN, new_y=YPos.NEXT,
                  fill=fill)

    def fila_tabla(self, concepto: str, valor_str: str, color_valor=None,
                   negrita_total: bool = False, bg=None):
        """Fila de la tabla de valores: concepto + monto tabular derecho."""
        fill = bg is not None
        if fill:
            self.set_fill_color(*bg)
        self.set_font("Helvetica", "B" if negrita_total else "", 9.5)
        self.cell(120, 8, concepto, fill=fill)
        if color_valor:
            self.set_text_color(*color_valor)
        self.set_font("Helvetica", "B", 9.5)
        self.cell(0, 8, valor_str + "  ", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=fill)
        self.set_text_color(*_TINTA)


def _fmt_cop(valor: float) -> str:
    """Formatea un número como pesos colombianos: ``$ 5.000.000``."""
    return "$ " + f"{valor:,.0f}".replace(",", ".")


def _fmt_cop_neg(valor: float) -> str:
    return "- $ " + f"{valor:,.0f}".replace(",", ".")


def _tarjeta_parte(pdf: _CuentaCobro, x: float, w: float, y: float,
                   titulo: str, lineas: list) -> float:
    """Tarjeta clara con título dorado y pares etiqueta–valor. Devuelve Y final.

    Los valores largos (razones sociales, direcciones) se envuelven en varias
    líneas en lugar de truncarse: en un documento legal el nombre completo
    importa.
    """
    w_val = w - 32
    pdf.set_font("Helvetica", "B", 8.5)
    alturas = [
        max(5.5, pdf.multi_cell(w_val, 5.5, str(val), dry_run=True,
                                output="HEIGHT"))
        for _, val in lineas
    ]
    h = 13 + sum(alturas)
    pdf.set_fill_color(*_SLATE_100)
    pdf.rect(x, y, w, h, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(x + 5, y + 4)
    pdf.etiqueta(titulo, _ORO)
    yy = pdf.get_y()
    for (etq, val), alto in zip(lineas, alturas):
        pdf.set_xy(x + 5, yy)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*_SLATE_500)
        pdf.cell(22, 5.5, etq)
        pdf.set_xy(x + 27, yy)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*_TINTA)
        pdf.multi_cell(w_val, 5.5, str(val), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        yy += alto
    return y + h


def generar_pdf(
    datos_freelancer: dict,
    datos_cliente: dict,
    valor: float,
    descripcion: str,
    numero: Optional[str] = None,
    fecha: Optional[date] = None,
    incluir_retencion: bool = True,
    tarifa_retencion: float = 0.11,
    incluir_ica: bool = False,
    valor_ica: float = 0.0,
    incluir_aportes: bool = False,
    aporte_salud: float = 0.0,
    aporte_pension: float = 0.0,
    info_bancaria_adicional: Optional[str] = None,
) -> bytes:
    """
    Genera una cuenta de cobro profesional en PDF.

    Args:
        datos_freelancer: Información del prestador.
            Requeridos: nombre, cedula.
            Opcionales: nit, ciudad, telefono, email, banco, cuenta,
                        tipo_cuenta, direccion, cargo.
        datos_cliente: Información del pagador.
            Requeridos: empresa, nit.
            Opcionales: contacto, ciudad, direccion, telefono.
        valor: Valor bruto del servicio en COP.
        descripcion: Descripción del servicio prestado.
        numero: Número del documento. Si es None, se genera con fecha.
        fecha: Fecha del documento. Default: hoy.
        incluir_retencion: Si True, muestra línea de retefuente.
        tarifa_retencion: Tarifa de retención (default 0.11 = 11%).
        incluir_ica: Si True, incluye línea de ReteICA.
        valor_ica: Monto de ICA ya calculado.
        incluir_aportes: Si True, muestra sección de aportes SGSS.
        aporte_salud: Monto aporte salud ya calculado.
        aporte_pension: Monto aporte pensión ya calculado.
        info_bancaria_adicional: Texto libre para instrucciones de pago.

    Returns:
        Bytes del PDF generado.

    Raises:
        ValueError: Si faltan campos obligatorios.

    Examples:
        >>> freelancer = {"nombre": "Ana García", "cedula": "52.123.456"}
        >>> cliente = {"empresa": "Tech Corp SAS", "nit": "900.123.456-7"}
        >>> pdf = generar_pdf(freelancer, cliente, 3_000_000,
        ...                   "Consultoría Sprint 3")
        >>> pdf[:4] == b'%PDF'
        True
    """
    # Validar obligatorios
    for campo in ["nombre", "cedula"]:
        if campo not in datos_freelancer:
            raise ValueError(f"datos_freelancer requiere '{campo}'")
    for campo in ["empresa", "nit"]:
        if campo not in datos_cliente:
            raise ValueError(f"datos_cliente requiere '{campo}'")

    fecha = fecha or date.today()
    meses_es = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
    }
    fecha_str = f"{fecha.day} de {meses_es[fecha.month]} de {fecha.year}"
    numero = numero or f"CC-{fecha.strftime('%Y%m%d')}"

    # Calcular valores
    valor_retencion = round(valor * tarifa_retencion) if incluir_retencion else 0
    total_descuentos = valor_retencion + valor_ica
    valor_neto = valor - total_descuentos

    # ── Construir documento ───────────────────────────────────────────────────
    pdf = _CuentaCobro(numero_doc=numero, fecha_doc=fecha_str)
    pdf.add_page()

    # ── PARTES: COBRADO POR / COBRADO A, lado a lado ─────────────────────────
    ciudad_doc = datos_freelancer.get("ciudad",
                                      datos_cliente.get("ciudad", "Colombia"))

    prestador_lineas = [("Nombre", datos_freelancer["nombre"]),
                        ("Cédula", datos_freelancer["cedula"])]
    if datos_freelancer.get("nit"):
        prestador_lineas.append(("NIT", datos_freelancer["nit"]))
    if datos_freelancer.get("cargo"):
        prestador_lineas.append(("Cargo", datos_freelancer["cargo"]))
    if datos_freelancer.get("ciudad"):
        prestador_lineas.append(("Ciudad", datos_freelancer["ciudad"]))
    if datos_freelancer.get("telefono"):
        prestador_lineas.append(("Teléfono", datos_freelancer["telefono"]))
    if datos_freelancer.get("email"):
        prestador_lineas.append(("Email", datos_freelancer["email"]))

    cliente_lineas = [("Razón social", datos_cliente["empresa"]),
                      ("NIT", datos_cliente["nit"])]
    if datos_cliente.get("contacto"):
        cliente_lineas.append(("Contacto", datos_cliente["contacto"]))
    if datos_cliente.get("ciudad"):
        cliente_lineas.append(("Ciudad", datos_cliente["ciudad"]))
    if datos_cliente.get("direccion"):
        cliente_lineas.append(("Dirección", datos_cliente["direccion"]))

    y0 = pdf.get_y()
    w_card = (_CONTENIDO - 6) / 2  # 86 mm por tarjeta
    y_izq = _tarjeta_parte(pdf, _MARGEN, w_card, y0, "Cobrado por",
                           prestador_lineas)
    y_der = _tarjeta_parte(pdf, _MARGEN + w_card + 6, w_card, y0, "Cobrado a",
                           cliente_lineas)
    pdf.set_y(max(y_izq, y_der) + 2)

    # Ciudad y fecha del documento, como línea informativa.
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_SLATE_500)
    pdf.cell(0, 6, f"{ciudad_doc}, {fecha_str}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_TINTA)

    # ── DESCRIPCIÓN DEL SERVICIO ──────────────────────────────────────────────
    pdf.titulo_seccion("Descripción del servicio")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_fill_color(*_SLATE_50)
    pdf.multi_cell(0, 6.5, "  " + descripcion, fill=True,
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── DESGLOSE DE VALORES ───────────────────────────────────────────────────
    pdf.titulo_seccion("Desglose de valores")

    pdf.set_fill_color(*_SLATE_900)
    pdf.set_text_color(*_BLANCO)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_char_spacing(0.5)
    pdf.cell(120, 8.5, "  CONCEPTO", fill=True)
    pdf.cell(0, 8.5, "VALOR (COP)  ", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_char_spacing(0)
    pdf.set_text_color(*_TINTA)

    pdf.fila_tabla("  Valor bruto del servicio", _fmt_cop(valor), bg=_SLATE_50)

    if incluir_retencion and valor_retencion > 0:
        tarifa_pct = f"{tarifa_retencion * 100:.0f}%"
        pdf.fila_tabla(
            f"  Retención en la fuente ({tarifa_pct} · Art. 392 E.T.)",
            _fmt_cop_neg(valor_retencion),
            color_valor=_ROJO,
        )

    if incluir_ica and valor_ica > 0:
        pdf.fila_tabla(
            "  ReteICA (Ley 14 de 1983)",
            _fmt_cop_neg(valor_ica),
            color_valor=_ROJO,
            bg=_SLATE_50,
        )

    # Caja de NETO A PAGAR: slate profundo, cifra dorada grande.
    pdf.ln(2)
    y_caja = pdf.get_y()
    pdf.set_fill_color(*_SLATE_900)
    pdf.rect(_MARGEN, y_caja, _CONTENIDO, 14, style="F", round_corners=True,
             corner_radius=3)
    pdf.set_xy(_MARGEN + 5, y_caja)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_char_spacing(0.5)
    pdf.set_text_color(*_BLANCO)
    pdf.cell(70, 14, "VALOR NETO A PAGAR")
    pdf.set_char_spacing(0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*_ORO)
    pdf.set_xy(_MARGEN, y_caja)
    pdf.cell(_CONTENIDO - 5, 14, _fmt_cop(valor_neto), align="R")
    pdf.set_text_color(*_TINTA)
    pdf.set_y(y_caja + 16)

    # ── APORTES A SEGURIDAD SOCIAL (informativo) ──────────────────────────────
    if incluir_aportes and (aporte_salud > 0 or aporte_pension > 0):
        pdf.titulo_seccion("Aportes a seguridad social (a cargo del prestador)")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*_SLATE_500)
        pdf.multi_cell(
            0, 4.5,
            "Los aportes a salud y pensión son obligación del prestador del servicio "
            "(Ley 1607 de 2012, Art. 26). Se calculan sobre el 40% del valor facturado (IBC).",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_text_color(*_TINTA)
        pdf.ln(1.5)
        pdf.fila_tabla("  Aporte a salud (12.5% del IBC)", _fmt_cop(aporte_salud),
                       bg=_SLATE_50)
        pdf.fila_tabla("  Aporte a pensión (16% del IBC)", _fmt_cop(aporte_pension))
        total_ap = aporte_salud + aporte_pension
        pdf.fila_tabla("  Total aportes", _fmt_cop(total_ap),
                       negrita_total=True, bg=_SLATE_50)

    # ── DATOS BANCARIOS ────────────────────────────────────────────────────────
    if datos_freelancer.get("banco") or info_bancaria_adicional:
        pdf.titulo_seccion("Datos bancarios para el pago")

        if datos_freelancer.get("banco"):
            pdf.fila_dato("Banco", datos_freelancer["banco"])
            tipo_cta = datos_freelancer.get("tipo_cuenta", "Ahorros")
            pdf.fila_dato("Tipo de cuenta", tipo_cta, bg_gris=True)
            if datos_freelancer.get("cuenta"):
                pdf.fila_dato("Número", datos_freelancer["cuenta"])
            pdf.fila_dato("Titular", datos_freelancer["nombre"], bg_gris=True)

        if info_bancaria_adicional:
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*_SLATE_500)
            pdf.multi_cell(0, 4.5, info_bancaria_adicional,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*_TINTA)

    # ── FIRMAS ────────────────────────────────────────────────────────────────
    pdf.ln(14)
    pdf.set_draw_color(*_SLATE_700)
    pdf.set_line_width(0.3)

    x_izq, x_der = 26, 118
    w_firma = 66
    y_firma = pdf.get_y()
    pdf.line(x_izq, y_firma, x_izq + w_firma, y_firma)
    pdf.line(x_der, y_firma, x_der + w_firma, y_firma)

    pdf.ln(2)
    nombre_prestador = datos_freelancer["nombre"][:28]
    nombre_pagador = datos_cliente.get("contacto", datos_cliente["empresa"])[:28]

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_x(x_izq)
    pdf.cell(w_firma, 5, nombre_prestador, align="C")
    pdf.set_x(x_der)
    pdf.cell(w_firma, 5, nombre_pagador, align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*_SLATE_500)
    pdf.set_x(x_izq)
    pdf.cell(w_firma, 5, "Prestador del servicio", align="C")
    pdf.set_x(x_der)
    pdf.cell(w_firma, 5, "Recibido / Autorizado", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_TINTA)

    return bytes(pdf.output())


def guardar_pdf(
    contenido: bytes,
    ruta: str,
) -> str:
    """
    Guarda el PDF en disco.

    Args:
        contenido: Bytes del PDF (resultado de generar_pdf()).
        ruta: Ruta del archivo de destino.

    Returns:
        Ruta del archivo guardado.

    Examples:
        >>> pdf = generar_pdf(...)
        >>> path = guardar_pdf(pdf, "cuenta_cobro_enero.pdf")
        >>> print(f"PDF guardado en: {path}")
    """
    with open(ruta, "wb") as f:
        f.write(contenido)
    return ruta
