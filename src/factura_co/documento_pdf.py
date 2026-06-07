"""
documento_pdf.py — Generador de cuentas de cobro profesionales en PDF.

Produce documentos PDF listos para imprimir o enviar por correo, con
diseño limpio y toda la información requerida por la regulación colombiana
para personas naturales no responsables de IVA.

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

# ── Paleta de colores ─────────────────────────────────────────────────────────
_AZUL_OSCURO  = (31, 73, 125)    # Encabezado principal
_AZUL_MEDIO   = (68, 114, 196)   # Subtítulos de sección
_AZUL_CLARO   = (214, 224, 245)  # Fondo de cabeceras de tabla
_GRIS_CLARO   = (245, 245, 245)  # Filas alternas
_GRIS_TEXTO   = (100, 100, 100)  # Texto secundario
_NEGRO        = (30, 30, 30)     # Texto principal
_VERDE        = (40, 160, 80)    # Neto a pagar (positivo)
_ROJO         = (192, 0, 0)      # Retenciones (descuento)
_BLANCO       = (255, 255, 255)



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
        "·": ".",   # punto medio
        " ": " ",   # espacio non-breaking
    }
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto

class _CuentaCobro(FPDF):
    """Subclase FPDF con header/footer personalizados."""

    def __init__(self, numero_doc: str, fecha_doc: str):
        super().__init__()
        self.numero_doc = numero_doc
        self.fecha_doc = fecha_doc
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=22)

    def normalize_text(self, txt):
        """Normaliza caracteres especiales a latin-1 seguro."""
        reemplazos = {
            "\u2014": "-",   # em dash
            "\u2013": "-",   # en dash
            "\u2018": "'",   # comilla izq
            "\u2019": "'",   # comilla der
            "\u201c": '"',   # doble izq
            "\u201d": '"',   # doble der
            "\u2026": "...", # ellipsis
            "\u00b7": ".",   # punto medio
            "\u00a0": " ",   # non-breaking space
        }
        for orig, remp in reemplazos.items():
            txt = txt.replace(orig, remp)
        return super().normalize_text(txt)

    def header(self):
        # Banda superior azul oscuro
        self.set_fill_color(*_AZUL_OSCURO)
        self.rect(0, 0, 210, 12, style="F")
        self.set_y(14)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_GRIS_TEXTO)
        self.set_draw_color(*_AZUL_MEDIO)
        self.set_line_width(0.3)
        self.line(18, self.get_y() - 2, 192, self.get_y() - 2)
        self.cell(0, 5, "Documento generado con factura-co | github.com/Brausin/factura-co", align="C")
        self.set_text_color(*_NEGRO)

    # ── Bloques reutilizables ─────────────────────────────────────────────────

    def titulo_seccion(self, texto: str):
        """Dibuja un encabezado de sección con fondo azul medio."""
        self.ln(4)
        self.set_fill_color(*_AZUL_MEDIO)
        self.set_text_color(*_BLANCO)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {texto.upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(*_NEGRO)
        self.ln(2)

    def fila_dato(self, etiqueta: str, valor: str, bg_gris: bool = False):
        """Dibuja una fila de dato etiqueta–valor."""
        if bg_gris:
            self.set_fill_color(*_GRIS_CLARO)
            fill = True
        else:
            fill = False
        self.set_font("Helvetica", "B", 9)
        self.cell(60, 6, etiqueta, fill=fill)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, valor, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=fill)

    def fila_tabla(self, concepto: str, valor_str: str, color_valor=None, negrita_total=False, bg=None):
        """Dibuja una fila en la tabla de valores."""
        if bg:
            self.set_fill_color(*bg)
            fill = True
        else:
            fill = False

        self.set_font("Helvetica", "B" if negrita_total else "", 9)
        self.cell(130, 7, concepto, fill=fill)

        if color_valor:
            self.set_text_color(*color_valor)
        self.set_font("Helvetica", "B" if negrita_total else "", 9)
        self.cell(0, 7, valor_str, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=fill)
        self.set_text_color(*_NEGRO)


def _fmt_cop(valor: float) -> str:
    """Formatea un número como pesos colombianos."""
    return f"$ {valor:>14,.0f}"


def _fmt_cop_neg(valor: float) -> str:
    return f"- $ {valor:>12,.0f}"


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

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    # Título grande
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_AZUL_OSCURO)
    pdf.cell(0, 12, "CUENTA DE COBRO", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Línea divisoria
    pdf.set_draw_color(*_AZUL_MEDIO)
    pdf.set_line_width(0.8)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(3)

    # Número y fecha en dos columnas
    pdf.set_text_color(*_NEGRO)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(95, 6, f"N° Documento:  {numero}")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Fecha:  {fecha_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    ciudad_doc = datos_freelancer.get("ciudad", datos_cliente.get("ciudad", "Colombia"))
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(95, 6, f"Ciudad:  {ciudad_doc}")
    pdf.ln(6)

    # ── DATOS FREELANCER ─────────────────────────────────────────────────────
    pdf.titulo_seccion("Cobrado por")
    pdf.fila_dato("Nombre:", datos_freelancer["nombre"])
    pdf.fila_dato("Cédula:", datos_freelancer["cedula"], bg_gris=True)
    if datos_freelancer.get("nit"):
        pdf.fila_dato("NIT:", datos_freelancer["nit"])
    if datos_freelancer.get("cargo"):
        pdf.fila_dato("Cargo:", datos_freelancer["cargo"], bg_gris=True)
    if datos_freelancer.get("ciudad"):
        pdf.fila_dato("Ciudad:", datos_freelancer["ciudad"])
    if datos_freelancer.get("telefono"):
        pdf.fila_dato("Teléfono:", datos_freelancer["telefono"], bg_gris=True)
    if datos_freelancer.get("email"):
        pdf.fila_dato("Email:", datos_freelancer["email"])

    # ── DATOS CLIENTE ─────────────────────────────────────────────────────────
    pdf.titulo_seccion("Cobrado a")
    pdf.fila_dato("Razón social:", datos_cliente["empresa"])
    pdf.fila_dato("NIT:", datos_cliente["nit"], bg_gris=True)
    if datos_cliente.get("contacto"):
        pdf.fila_dato("Contacto:", datos_cliente["contacto"])
    if datos_cliente.get("ciudad"):
        pdf.fila_dato("Ciudad:", datos_cliente["ciudad"], bg_gris=True)
    if datos_cliente.get("direccion"):
        pdf.fila_dato("Dirección:", datos_cliente["direccion"])

    # ── DESCRIPCIÓN DEL SERVICIO ──────────────────────────────────────────────
    pdf.titulo_seccion("Descripción del servicio")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_fill_color(*_GRIS_CLARO)
    pdf.multi_cell(0, 7, descripcion, fill=True)
    pdf.ln(2)

    # ── TABLA DE VALORES ──────────────────────────────────────────────────────
    pdf.titulo_seccion("Desglose de valores")

    # Cabecera de tabla
    pdf.set_fill_color(*_AZUL_CLARO)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(130, 7, "  Concepto", fill=True)
    pdf.cell(0, 7, "Valor (COP)", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)

    # Valor bruto
    pdf.fila_tabla("  Valor bruto del servicio", _fmt_cop(valor), bg=_GRIS_CLARO)

    # Retención en la fuente
    if incluir_retencion and valor_retencion > 0:
        tarifa_pct = f"{tarifa_retencion * 100:.0f}%"
        pdf.fila_tabla(
            f"  Retención en la fuente ({tarifa_pct} — Art. 392 E.T.)",
            _fmt_cop_neg(valor_retencion),
            color_valor=_ROJO,
        )

    # ReteICA
    if incluir_ica and valor_ica > 0:
        pdf.fila_tabla(
            "  ReteICA (Ley 14 de 1983)",
            _fmt_cop_neg(valor_ica),
            color_valor=_ROJO,
            bg=_GRIS_CLARO,
        )

    # Separador
    pdf.set_draw_color(*_AZUL_MEDIO)
    pdf.set_line_width(0.3)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())

    # NETO A PAGAR
    pdf.set_fill_color(230, 245, 235)  # Verde muy suave
    pdf.fila_tabla(
        "  VALOR NETO A PAGAR",
        _fmt_cop(valor_neto),
        color_valor=_VERDE,
        negrita_total=True,
        bg=(230, 245, 235),
    )
    pdf.ln(2)

    # ── APORTES A SEGURIDAD SOCIAL (informativo) ──────────────────────────────
    if incluir_aportes and (aporte_salud > 0 or aporte_pension > 0):
        pdf.titulo_seccion("Aportes a seguridad social (a cargo del prestador)")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*_GRIS_TEXTO)
        pdf.multi_cell(
            0, 5,
            "Los aportes a salud y pensión son obligación del prestador del servicio "
            "(Ley 1607 de 2012, Art. 26). Se calculan sobre el 40% del valor facturado (IBC).",
        )
        pdf.set_text_color(*_NEGRO)
        pdf.ln(2)
        pdf.fila_tabla("  Aporte a salud (12.5% del IBC)", _fmt_cop(aporte_salud), bg=_GRIS_CLARO)
        pdf.fila_tabla("  Aporte a pensión (16% del IBC)", _fmt_cop(aporte_pension))
        total_ap = aporte_salud + aporte_pension
        pdf.fila_tabla(
            "  Total aportes",
            _fmt_cop(total_ap),
            negrita_total=True,
            bg=_GRIS_CLARO,
        )
        pdf.ln(2)

    # ── DATOS BANCARIOS ────────────────────────────────────────────────────────
    if datos_freelancer.get("banco") or info_bancaria_adicional:
        pdf.titulo_seccion("Datos bancarios para el pago")

        if datos_freelancer.get("banco"):
            pdf.fila_dato("Banco:", datos_freelancer["banco"])
            tipo_cta = datos_freelancer.get("tipo_cuenta", "Ahorros")
            pdf.fila_dato("Tipo de cuenta:", tipo_cta, bg_gris=True)
            if datos_freelancer.get("cuenta"):
                pdf.fila_dato("Número:", datos_freelancer["cuenta"])
            pdf.fila_dato("Titular:", datos_freelancer["nombre"], bg_gris=True)

        if info_bancaria_adicional:
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*_GRIS_TEXTO)
            pdf.multi_cell(0, 5, info_bancaria_adicional)
            pdf.set_text_color(*_NEGRO)

    # ── FIRMAS ────────────────────────────────────────────────────────────────
    pdf.ln(10)
    pdf.set_draw_color(*_NEGRO)
    pdf.set_line_width(0.3)

    # Dos líneas de firma
    x_izq, x_der = 30, 120
    y_firma = pdf.get_y()
    pdf.line(x_izq, y_firma, x_izq + 65, y_firma)
    pdf.line(x_der, y_firma, x_der + 65, y_firma)

    pdf.ln(2)
    nombre_prestador = datos_freelancer["nombre"][:28]
    nombre_pagador = datos_cliente.get("contacto", datos_cliente["empresa"])[:28]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(x_izq)
    pdf.cell(65, 5, nombre_prestador, align="C")
    pdf.set_x(x_der)
    pdf.cell(65, 5, nombre_pagador, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*_GRIS_TEXTO)
    pdf.set_x(x_izq)
    pdf.cell(65, 5, "Prestador del servicio", align="C")
    pdf.set_x(x_der)
    pdf.cell(65, 5, "Recibido / Autorizado", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_NEGRO)

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
