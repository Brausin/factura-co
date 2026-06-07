"""
ejemplo_arrendamiento.py
==========================
Arrendamiento de local comercial a empresa pagadora.

CONTEXTO TRIBUTARIO:
    El arrendamiento de inmuebles está sujeto a retención en la fuente
    según el Artículo 401 del Estatuto Tributario. A diferencia de
    honorarios y servicios, en el arrendamiento:

    1. RETENCIÓN EN LA FUENTE (Art. 401 E.T.):
       - Tarifa ÚNICA: 3.5% sin importar si el arrendador declara renta
       - Sin base mínima: aplica desde el primer peso
       - El arrendatario (empresa que paga el arriendo) retiene y consigna

    2. APORTES A SEGURIDAD SOCIAL:
       - Los arrendadores personas naturales que reciben renta de capital
         (no de trabajo) NO están obligados a cotizar a seguridad social
         por concepto de arrendamiento (Circular UGPP 01/2023).
       - EXCEPCIÓN: si el arrendamiento es la actividad económica principal
         del contribuyente (arrendador de varios inmuebles), puede aplicar
         la obligación de cotizar. Consultar con asesor tributario.

    3. IMPUESTO DE INDUSTRIA Y COMERCIO (ICA):
       - El arrendamiento de inmuebles puede generar ICA si se realiza
         de manera habitual y en el municipio de la actividad.
       - Para persona natural no comerciante con un solo inmueble,
         generalmente NO aplica ICA.

    4. IMPUESTO PREDIAL e IVA:
       - El arrendamiento de inmuebles para uso comercial puede estar
         gravado con IVA (19%) si el arrendador es responsable del IVA.
       - Este ejemplo asume arrendador no responsable de IVA.

CASO:
    Propietario persona natural arrienda local comercial en Bogotá por
    $4.500.000 mensuales a empresa de retail.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.factura_co.retenciones import calcular_retencion
from src.factura_co.documento import generar_documento_txt

CANON_MENSUAL = 4_500_000   # Arriendo mensual

print("=" * 65)
print("  EJEMPLO: ARRENDAMIENTO DE LOCAL COMERCIAL")
print("=" * 65)
print(f"  Canon mensual:    ${CANON_MENSUAL:,.0f}")
print(f"  Tipo retención:   arrendamiento (Art. 401 E.T.)")
print()

# ── Cálculo de retención ──────────────────────────────────────────────────────
# Nota: declarante y no declarante tienen la MISMA tarifa (3.5%)
r_no_dec = calcular_retencion(CANON_MENSUAL, "arrendamiento", es_declarante=False)
r_dec = calcular_retencion(CANON_MENSUAL, "arrendamiento", es_declarante=True)

print("  RETENCIÓN EN LA FUENTE:")
print(f"    Tarifa:           {r_no_dec['tarifa_pct']}  (igual para declarantes y no declarantes)")
print(f"    Valor retenido:   ${r_no_dec['valor_retencion']:,.0f}")
print(f"    Valor recibido:   ${r_no_dec['valor_neto']:,.0f}")
print(f"    Referencia:       {r_no_dec['articulo_et']}")
print()

# ── Sin aportes en arrendamiento ─────────────────────────────────────────────
print("  APORTES A SEGURIDAD SOCIAL:")
print("    Para arrendamiento de UN inmueble como renta pasiva,")
print("    la persona natural NO está obligada a cotizar al SGSS.")
print("    (Circular UGPP 01/2023 — art. 135 Ley 1753 de 2015)")
print()

# ── Resultado final ───────────────────────────────────────────────────────────
neto = r_no_dec["valor_neto"]   # Sin aportes
pct = neto / CANON_MENSUAL * 100
print("  RESUMEN MENSUAL:")
print(f"    Canon acordado:               ${CANON_MENSUAL:>12,.0f}")
print(f"    - Retención (3.5%):           -${r_no_dec['valor_retencion']:>11,.0f}")
print(f"    Valor que transfiere empresa:  ${neto:>12,.0f}  ({pct:.1f}%)")
print()

# ── Proyección anual ──────────────────────────────────────────────────────────
print("  PROYECCIÓN ANUAL (12 meses):")
print(f"    Ingreso bruto anual:   ${CANON_MENSUAL * 12:>14,.0f}")
print(f"    Retenciones anuales:   ${r_no_dec['valor_retencion'] * 12:>14,.0f}")
print(f"    Ingreso neto anual:    ${neto * 12:>14,.0f}")
print()

# ── Escenario de arrendamiento bajo ($800.000) ────────────────────────────────
canon_bajo = 800_000
r_bajo = calcular_retencion(canon_bajo, "arrendamiento")
print(f"  CONTRASTE — Canon bajo (${canon_bajo:,.0f}):")
print(f"    Retención (3.5%): ${r_bajo['valor_retencion']:,.0f}")
print(f"    Neto:             ${r_bajo['valor_neto']:,.0f}")
print(f"    Nota: sin base mínima → aplica desde el primer peso")
print()

# ── Generar documento de cobro ────────────────────────────────────────────────
arrendador = {
    "nombre": "Hector Morales Pinto",
    "cedula": "17.456.789",
    "ciudad": "Bogota",
    "banco": "Bancolombia",
    "cuenta": "445-678901-23",
    "tipo_cuenta": "Ahorros",
}
arrendatario = {
    "empresa": "Distribuidora Nacional S.A.S.",
    "nit": "830.456.789-1",
    "contacto": "Lucia Perez",
    "ciudad": "Bogota",
    "direccion": "Cra. 15 # 93-47, Bogota",
}

doc = generar_documento_txt(
    datos_freelancer=arrendador,
    datos_cliente=arrendatario,
    valor=CANON_MENSUAL,
    descripcion=(
        "Arrendamiento de local comercial ubicado en Cra. 7 # 45-12, "
        "Bogota D.C. Piso 1. Area: 80 m2. Correspondiente al mes de "
        "octubre de 2024."
    ),
    numero="ARR-2024-10",
    incluir_retencion=True,
)

print("  DOCUMENTO DE COBRO (vista previa):")
print("  " + "-" * 63)
# Mostrar solo las primeras líneas
for linea in doc.split("\n")[:20]:
    print("  " + linea)
print("  ...")
print()
print("  NOTA FINAL:")
print("    El recibo de arrendamiento no es factura ni cuenta de cobro")
print("    de servicios — es un comprobante de pago de renta de capital.")
print("    La retención la practica el ARRENDATARIO (empresa que paga),")
print("    no el arrendador. El arrendador solo recibe el neto.")
