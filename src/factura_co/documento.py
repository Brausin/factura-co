"""
documento.py — Generador de documentos de cobro para freelancers colombianos.

Genera una cuenta de cobro o documento de cobro en texto plano (.txt)
que puede enviarse por correo o imprimirse para cobrar servicios prestados.

El documento de cobro (o "cuenta de cobro") es el documento válido para
freelancers que no están obligados a facturar electrónicamente, según
la regulación de la DIAN para personas naturales no responsables de IVA.
"""

from datetime import date
from typing import Optional


def generar_documento_txt(
    datos_freelancer: dict,
    datos_cliente: dict,
    valor: float,
    descripcion: str,
    numero: Optional[str] = None,
    fecha: Optional[date] = None,
    incluir_retencion: bool = True,
) -> str:
    """
    Genera un documento de cobro en texto plano.

    Args:
        datos_freelancer: Información del prestador del servicio.
            Campos requeridos:
                - nombre: nombre completo
                - cedula: número de documento
            Campos opcionales:
                - banco: nombre del banco
                - cuenta: número de cuenta
                - tipo_cuenta: "Ahorros" o "Corriente" (por defecto "Ahorros")
                - ciudad: ciudad de residencia
                - telefono: número de contacto
                - email: correo electrónico
        datos_cliente: Información del pagador.
            Campos requeridos:
                - empresa: nombre o razón social
                - nit: NIT o cédula del pagador
            Campos opcionales:
                - contacto: nombre del contacto en la empresa
                - ciudad: ciudad
                - direccion: dirección física
        valor: Valor del servicio en pesos colombianos.
        descripcion: Descripción del servicio prestado.
        numero: Número del documento (ej. "001", "DC-2024-05"). Si no se
            especifica, se usa la fecha en formato YYYYMMDD.
        fecha: Fecha del documento. Por defecto la fecha actual.
        incluir_retencion: Si True, muestra la retención estimada (11%).

    Returns:
        String con el documento formateado listo para guardar o imprimir.

    Raises:
        ValueError: Si faltan campos obligatorios en datos_freelancer o datos_cliente.

    Examples:
        >>> freelancer = {"nombre": "Ana García", "cedula": "1234567890",
        ...               "banco": "Bancolombia", "cuenta": "123-456789-00"}
        >>> cliente = {"empresa": "Tech Corp SAS", "nit": "900.123.456-7"}
        >>> doc = generar_documento_txt(freelancer, cliente, 3_000_000,
        ...                             "Desarrollo de módulo de login")
        >>> "CUENTA DE COBRO" in doc
        True
        >>> "Ana García" in doc
        True
    """
    # Validar campos obligatorios
    for campo in ["nombre", "cedula"]:
        if campo not in datos_freelancer:
            raise ValueError(f"datos_freelancer requiere el campo '{campo}'")
    for campo in ["empresa", "nit"]:
        if campo not in datos_cliente:
            raise ValueError(f"datos_cliente requiere el campo '{campo}'")

    fecha = fecha or date.today()
    numero = numero or fecha.strftime("%Y%m%d")

    # Calcular retención estimada
    tarifa_retencion = 0.11
    valor_retencion = round(valor * tarifa_retencion) if incluir_retencion else 0
    valor_neto = valor - valor_retencion

    sep_doble = "=" * 65
    sep_simple = "-" * 65

    lineas = [
        sep_doble,
        " " * 20 + "CUENTA DE COBRO",
        sep_doble,
        "",
        f"  Número:  {numero}",
        f"  Fecha:   {fecha.strftime('%d de %B de %Y')}",
        f"  Ciudad:  {datos_freelancer.get('ciudad', datos_cliente.get('ciudad', 'Colombia'))}",
        "",
        sep_simple,
        "  COBRADO POR:",
        sep_simple,
        f"  Nombre:     {datos_freelancer['nombre']}",
        f"  Cédula:     {datos_freelancer['cedula']}",
    ]

    if "email" in datos_freelancer:
        lineas.append(f"  Email:      {datos_freelancer['email']}")
    if "telefono" in datos_freelancer:
        lineas.append(f"  Teléfono:   {datos_freelancer['telefono']}")

    lineas += [
        "",
        sep_simple,
        "  COBRADO A:",
        sep_simple,
        f"  Empresa:    {datos_cliente['empresa']}",
        f"  NIT:        {datos_cliente['nit']}",
    ]

    if "contacto" in datos_cliente:
        lineas.append(f"  Contacto:   {datos_cliente['contacto']}")
    if "direccion" in datos_cliente:
        lineas.append(f"  Dirección:  {datos_cliente['direccion']}")

    lineas += [
        "",
        sep_simple,
        "  DESCRIPCIÓN DEL SERVICIO:",
        sep_simple,
        f"  {descripcion}",
        "",
        sep_simple,
        "  VALOR:",
        sep_simple,
        f"  Valor bruto:                    ${valor:>15,.0f}",
    ]

    if incluir_retencion:
        lineas += [
            f"  Retención en la fuente (11%):  -${valor_retencion:>14,.0f}",
            f"  {'-' * 47}",
            f"  VALOR NETO A PAGAR:             ${valor_neto:>15,.0f}",
        ]
    else:
        lineas.append(f"  VALOR TOTAL A PAGAR:            ${valor:>15,.0f}")

    if "banco" in datos_freelancer:
        lineas += [
            "",
            sep_simple,
            "  DATOS BANCARIOS PARA EL PAGO:",
            sep_simple,
            f"  Banco:          {datos_freelancer['banco']}",
        ]
        if "tipo_cuenta" in datos_freelancer:
            lineas.append(f"  Tipo de cuenta: {datos_freelancer['tipo_cuenta']}")
        else:
            lineas.append("  Tipo de cuenta: Ahorros")
        if "cuenta" in datos_freelancer:
            lineas.append(f"  Número:         {datos_freelancer['cuenta']}")
        lineas.append(f"  Titular:        {datos_freelancer['nombre']}")

    lineas += [
        "",
        sep_simple,
        "  FIRMAS:",
        sep_simple,
        "",
        "",
        "  ________________________         ________________________",
        f"  {datos_freelancer['nombre'][:24]:<24}   {datos_cliente.get('contacto', datos_cliente['empresa'])[:24]:<24}",
        "  Prestador del servicio           Representante del pagador",
        "",
        sep_doble,
        "  Documento generado con factura-co | github.com/Brausin/factura-co",
        sep_doble,
    ]

    return "\n".join(lineas)


def guardar_documento(
    contenido: str,
    ruta: str,
) -> str:
    """
    Guarda el documento de cobro en un archivo de texto.

    Args:
        contenido: Texto del documento (resultado de generar_documento_txt).
        ruta: Ruta donde guardar el archivo (ej. "cobro_enero.txt").

    Returns:
        Ruta del archivo guardado.

    Examples:
        >>> doc = generar_documento_txt(...)
        >>> path = guardar_documento(doc, "cobro_2024_01.txt")
        >>> print(f"Guardado en: {path}")
    """
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta
