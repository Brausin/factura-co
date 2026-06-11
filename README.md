<div align="center">

# 💼 factura-co

*La calculadora de facturación para freelancers colombianos que cobran en dólares.*

![Tests](https://img.shields.io/badge/tests-152%20passing-brightgreen?style=flat-square&logo=pytest)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![TRM](https://img.shields.io/badge/TRM-tiempo%20real-orange?style=flat-square)
![Plataformas](https://img.shields.io/badge/plataformas-9-purple?style=flat-square)
![Fiscal](https://img.shields.io/badge/normativa-2026%20vigente-22C55E?style=flat-square)

*¿Cuánto te llegó realmente? ¿Cuánto debiste cobrar? ¿Cuánto guardar para impuestos?*

</div>

---

## El problema

Eres freelancer en Colombia y cobras en dólares. Un cliente te paga USD 1.000, pero a tu cuenta nunca llegan los USD 1.000 × TRM que esperabas: PayPal te muerde un 3,5 % más un spread de cambio del 2,5 %, Wise casi nada, Payoneer algo intermedio. Encima toca restar la retención en la fuente, los aportes a seguridad social como independiente y separar plata para la declaración de renta. El resultado es que casi nadie sabe **cuánto le va a llegar de verdad**, **cuánto debió cobrar** para que le quedara lo que necesita, ni **cuánto guardar** para no quedar debiendo en abril. `factura-co` responde esas tres preguntas con números, no con suposiciones.

## Actualizado a la normativa 2026

Los cálculos usan los valores fiscales **vigentes**, no los del año pasado:

| Parámetro | Valor 2026 | Fuente oficial |
|-----------|-----------|----------------|
| UVT | **$52.374** | Resolución DIAN 000238 de 2025 |
| SMMLV | **$1.750.905** | Decreto 1469 de 2025 |
| Tabla de renta | Art. 241 ET (rangos en UVT) | Estatuto Tributario |

El historial completo de UVT (2015–2026) vive en [`data/uvt_history.json`](data/uvt_history.json) y el código expone los alias `UVT_VIGENTE` y `SMMLV_VIGENTE`, de modo que actualizar el año entrante es tocar un solo archivo.

## La app

Interfaz Streamlit con sistema de diseño **dark OLED fintech** (fondo `#020617`, CTA verde, tipografía IBM Plex Sans, iconos SVG):

| Página | Qué hace |
|--------|----------|
| **Inicio** | Indicadores del día: TRM en vivo, mejor plataforma para US$1.000 y SMMLV en dólares. |
| **Plataformas** | Comisión real y neto en pesos de un pago internacional, con simulador de TRM y resumen copiable para el cliente. |
| **Comparador** | Ranking de las 9 plataformas para un mismo pago + exportación a CSV. |
| **Calculadora** | Cálculo inverso: cuánto facturar para recibir un neto objetivo. |
| **Proyección** | Renta anual estimada (Art. 241 ET) con gráficas y exportación a CSV. |
| **Factura** | Factura profesional en PDF lista para enviar. |
| **Cuenta de cobro** | El documento equivalente para no obligados a facturar electrónicamente (Res. DIAN 000042 de 2020), con retención y aportes opcionales. |

```bash
streamlit run app/main.py
```

## Características de la librería

| Módulo | Qué hace |
|--------|----------|
| 🌐 `trm_live` | TRM del día en tiempo real con **3 fuentes y fallback** (datos.gov.co → exchangerate-api → estimado), marcando si el dato es oficial o estimado. |
| 💸 `plataformas` | Comisiones **reales** de 9 plataformas de pago: porcentaje, costo fijo y spread de cambio. |
| ⚖️ `comparador` | Rankea las 9 plataformas y te dice exactamente cuántos pesos recibes con cada una. |
| 🎯 `calculadora` | Cálculo **inverso** por búsqueda binaria: cuánto facturar para que te queden $X netos. |
| 📈 `proyeccion` | Proyección anual con retención, aportes e impuesto de renta usando la UVT vigente. |
| 🧾 `retenciones` | Retención en la fuente por tipo de servicio (Art. 392/401 ET) e ICA por municipio. |
| 🏥 `aportes` | Aportes a salud y pensión del independiente (IBC 40 %, pisos y techos 2026). |
| 📄 `factura_pdf` / `documento_pdf` | Factura y cuenta de cobro en **PDF** con `fpdf2`, sin dependencias pesadas. |

## Plataformas soportadas

Comisión aproximada total (comisión + spread de cambio) para un pago típico:

| Plataforma | Comisión real | Mejor para |
|------------|---------------|------------|
| **Wise (TransferWise)** | ~0,7 % (0,41 % + 0,3 % FX) | La mejor tasa global; montos medianos y altos. |
| **Binance P2P** | ~1,1 % (0,1 % + 1 % FX) | Cobrar en USDT/cripto con liquidación rápida. |
| **Buda.com** | ~1,3 % (0,8 % + 0,5 % FX) | Cripto regulado y local en Colombia. |
| **Nequi Internacional** | ~3,5 % (2 % + 1,5 % FX) | Recibir directo en Nequi / Bancolombia. |
| **Payoneer** | ~4 % (2 % + 2 % FX) | Retiros desde marketplaces (Upwork, Fiverr). |
| **PayPal** | ~6 % (3,49 % + $0,49 + 2,5 % FX) | Clientes que solo pagan por PayPal. |
| **Upwork** | 10 % (escalonada por historial) | Conseguir clientes dentro de la plataforma. |
| **Freelancer.com** | 10 % (mínimo $5 USD) | Proyectos pequeños dentro de la plataforma. |
| **SWIFT / Wire** | $25 fijo + 3 % FX | Transferencias corporativas muy grandes (el fijo se diluye). |

## Instalación

```bash
# 1. Clonar e instalar
git clone https://github.com/Brausin/factura-co.git
cd factura-co
pip install -e .

# 2. Abrir la app interactiva (Streamlit)
streamlit run app/main.py

# 3. Correr la batería de pruebas
pytest -q          # 152 passing
```

## Uso rápido

```python
# 1) TRM de hoy en tiempo real
from factura_co.trm_live import get_trm_hoy, get_trm_info

trm = get_trm_hoy()
print(f"1 USD = {trm:,.2f} COP")

info = get_trm_info()
print(info["fuente"], "| estimado:", info["es_estimado"])
```

```python
# 2) ¿Cuánto me queda si cobro USD 1.000 por Wise?
from factura_co.plataformas import calcular_neto_plataforma

r = calcular_neto_plataforma(1000, "wise", trm)
print(f"Recibes ${r['valor_cop']:,.0f} COP (costo {r['costo_total_pct']} %)")
```

```python
# 3) Comparar las 9 plataformas y quedarme con la mejor
from factura_co.comparador import comparar_plataformas

ranking = comparar_plataformas(1000, trm)
mejor = ranking[0]
print(f"Mejor opción: {mejor['plataforma']} → ${mejor['valor_cop']:,.0f} COP")
```

```python
# 4) Cálculo inverso: ¿cuánto facturar para recibir $3.000.000 netos?
from factura_co.calculadora import calcular_bruto_necesario

r = calcular_bruto_necesario(3_000_000, "honorarios",
                             es_declarante=True, incluir_aportes=True)
print(f"Factura ${r['bruto_necesario']:,.0f} para que te queden $3.000.000 limpios")
```

```python
# 5) Generar la factura en PDF
from factura_co.factura_pdf import generar_factura

pdf = generar_factura({
    "nombre_freelancer": "Juan Pérez", "nit_freelancer": "1.234.567",
    "nombre_cliente": "Acme Inc.", "nit_cliente": "900.123.456",
    "descripcion_servicio": "Desarrollo de software", "valor_cop": 3_816_795,
    "retencion_pct": 0.11, "fecha": "2026-06-10", "numero_factura": "FCO-2026-001",
})
open("factura.pdf", "wb").write(pdf)   # PDF válido (%PDF...)
```

## Automatización

| Workflow | Qué hace | Frecuencia |
|----------|----------|------------|
| [`ci.yml`](.github/workflows/ci.yml) | Corre la batería de pruebas en cada push. | Por push |
| [`actualizar_trm.yml`](.github/workflows/actualizar_trm.yml) | Refresca la TRM de respaldo desde datos.gov.co. | Diaria |
| [`actualizar_tablas.yml`](.github/workflows/actualizar_tablas.yml) | Mantiene al día las tablas de retención. | Programada |

## Estructura

```
factura-co/
├── src/factura_co/
│   ├── trm_live.py        # TRM en tiempo real (3 fuentes + fallback)
│   ├── plataformas.py     # 9 plataformas: comisiones reales
│   ├── comparador.py      # ranking de plataformas
│   ├── calculadora.py     # cálculo inverso (búsqueda binaria)
│   ├── proyeccion.py      # proyección anual + renta (UVT vigente)
│   ├── retenciones.py     # retención en la fuente + ICA + historial UVT
│   ├── aportes.py         # aportes SGSS del independiente (SMMLV 2026)
│   ├── factura_pdf.py     # factura en PDF (fpdf2)
│   └── documento_pdf.py   # cuenta de cobro en PDF
├── app/
│   ├── main.py            # app Streamlit (7 páginas)
│   └── ui.py              # sistema de diseño dark OLED fintech
├── data/
│   ├── tablas_retencion_2025.json
│   └── uvt_history.json   # UVT 2015–2026 con resolución DIAN de cada año
├── examples/              # 7 ejemplos ejecutables
├── scripts/               # CLI de cálculo y actualizadores de UVT/TRM
└── tests/                 # 152 pruebas (incluye AppTest de la app)
```

## Stack

| Capa | Tecnología | Para qué |
|------|-----------|----------|
| Lógica | **Python 3.11+** | cálculo de comisiones, retención, aportes y renta |
| Interfaz | **Streamlit** | app web interactiva de 7 páginas |
| Gráficas | **Plotly** | comparativos y proyecciones |
| Documentos | **fpdf2** | facturas y cuentas de cobro en PDF |
| Calidad | **pytest** | 152 pruebas automatizadas |
| Datos | **datos.gov.co · DIAN · MinTrabajo** | TRM oficial y normativa vigente |

> **Nota:** las cifras son estimaciones para planear; no constituyen asesoría
> tributaria. Para tu declaración real, consulta un contador.

## Hermanos de familia

| Proyecto | Qué resuelve |
|----------|--------------|
| [propuesta-co](https://github.com/Brausin/propuesta-co) | Cotizar bien y entregar propuestas en PDF que se ven profesionales. |
| [colombia-data-insights](https://github.com/Brausin/colombia-data-insights) | TRM, inflación, desempleo y exportaciones de Colombia en dashboard, librería y API. |

---

MIT © 2024–2026 Brausin
