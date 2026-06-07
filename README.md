# 🧾 factura-co

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/Brausin/factura-co/actions/workflows/ci.yml/badge.svg)](https://github.com/Brausin/factura-co/actions)
[![Version](https://img.shields.io/badge/version-0.2.0-orange)](https://github.com/Brausin/factura-co)

**Calculadora de retenciones, aportes y generador de documentos de cobro para freelancers colombianos.**

> Porque cobrar bien no debería ser un trabajo de tiempo completo.

---

## ¿Por qué factura-co?

Trabajar como freelancer en Colombia tiene sus complicaciones. Tres dolores que casi todos los independientes han vivido:

**1. La retención en la fuente: ese porcentaje misterioso**
Tu cliente te dice "te retengo el 11%" y tú asientes... pero ¿es correcto? ¿Es el 10%? ¿El 6%? ¿Depende del servicio o del valor? La respuesta está en el Estatuto Tributario, no en el Excel del contador que te cobró $200.000 por revisarlo.

**2. Salud y pensión: ¿cuánto debo pagar este mes?**
Como independiente, pagas tus propios aportes. El cálculo es sobre el 40% del ingreso. Pero... ¿el 40% de qué? ¿Del valor bruto? ¿Después de la retención? ¿Hay un mínimo? Muchos freelancers pagan de más, otros de menos, y pocos lo hacen bien.

**3. ¿Cuánto me va a quedar realmente?**
Antes de decirle el precio a un cliente, necesitas saber cuánto te va a llegar al bolsillo. Sin esa claridad, terminas trabajando por menos de lo que pensabas.

**factura-co resuelve los tres con una sola línea de código.**

---

## ¿Qué hace?

Dado el valor de una factura, `factura-co` calcula:

| Concepto | Ejemplo ($5.000.000 en honorarios) |
|---|---|
| Valor bruto | $5.000.000 |
| Retención en la fuente (11%) | -$550.000 |
| IBC — base cotización (40%) | $2.000.000 |
| Aporte salud (12.5%) | -$250.000 |
| Aporte pensión (16%) | -$320.000 |
| **Ingreso neto real** | **$3.880.000** |

```python
from factura_co.calculadora import calcular_neto, generar_resumen

resultado = calcular_neto(5_000_000, "honorarios")
generar_resumen(resultado)
```

---

## Instalación

```bash
git clone https://github.com/Brausin/factura-co.git
cd factura-co
pip install -e .

# Dependencias de la app web y CLI
pip install -r requirements-app.txt
```

---

## Uso rápido

### CLI — desde la terminal

```bash
# Cálculo básico
python scripts/calcular.py --valor 3000000 --tipo honorarios

# Declarante de renta (tarifa 10% en lugar de 11%)
python scripts/calcular.py --valor 8000000 --tipo honorarios --declarante

# Exportar resultado a JSON
python scripts/calcular.py --valor 5000000 --exportar

# Generar cuenta de cobro TXT (interactivo)
python scripts/calcular.py --valor 5000000 --documento

# Ver todos los tipos de servicio y tarifas
python scripts/calcular.py --listar-tipos

# Versión
python scripts/calcular.py --version
```

### App web (Streamlit)

```bash
make run-app
# o directamente:
streamlit run app/main.py
```

La app incluye:
- Sidebar con todos los parámetros (tipo, declarante, aportes, ReteICA)
- Desglose visual en columnas (retenciones | seguridad social)
- **Neto a recibir** destacado en verde
- Descarga de cuenta de cobro en TXT y PDF con un clic
- Sección educativa con tablas de tarifas e historial UVT

### API Python

```python
from factura_co.calculadora import calcular_neto
from factura_co.retenciones import calcular_ica, obtener_uvt
from factura_co.documento_pdf import generar_pdf

# Cálculo completo
resultado = calcular_neto(5_000_000, "honorarios", es_declarante=True)
print(resultado["neto"])          # ingreso disponible
print(resultado["neto_pct"])      # % del bruto

# ICA (Bogotá, servicios profesionales — 9.66‰)
ica = calcular_ica(5_000_000, "bogota", "servicios_profesionales")
print(ica["valor_ica"])           # 48.300

# UVT por año
print(obtener_uvt(2024))          # 47.065
print(obtener_uvt(2025))          # 49.799

# Generar PDF
pdf = generar_pdf(
    datos_freelancer={"nombre": "Juan Vargas", "cedula": "79.123.456"},
    datos_cliente={"empresa": "Cliente SAS", "nit": "900.000.001-1"},
    valor=5_000_000,
    descripcion="Consultoría en transformación digital",
)
with open("cuenta_cobro.pdf", "wb") as f:
    f.write(pdf)
```

---

## Tipos de servicio y tarifas

| Tipo | Descripción | No declarante | Declarante | Base mínima |
|---|---|---|---|---|
| `honorarios` | Servicios profesionales, técnicos | **11%** | 10% | Sin mínimo |
| `servicios` | Servicios generales | **6%** | 4% | 4 UVT |
| `arrendamiento` | Arriendo de bienes | **3.5%** | 3.5% | Sin mínimo |
| `compras` | Compra de bienes | **3.5%** | 2.5% | 27 UVT |
| `transporte` | Transporte nacional | **3.5%** | 3.5% | 27 UVT |

> **¿Declarante?** Si tus ingresos anuales superan ~1.400 UVT (~$69.7M en 2025), declaras renta.

---

## Historial UVT (2015–2025)

| Año | Valor UVT | Resolución DIAN |
|---|---|---|
| 2015 | $28.279 | Res. 000228/2014 |
| 2020 | $35.607 | Res. 000084/2019 |
| 2023 | $42.412 | Res. 000178/2022 |
| 2024 | $47.065 | Res. 000187/2023 |
| **2025** | **$49.799** | **Res. 000186/2024** |

Ver historial completo: [`data/uvt_history.json`](data/uvt_history.json)

---

## Estructura del proyecto

```
factura-co/
├── src/factura_co/
│   ├── retenciones.py      # Retefuente, ICA, historial UVT
│   ├── aportes.py          # Salud, pensión, IBC
│   ├── calculadora.py      # Cálculo integrado neto
│   ├── documento.py        # Cuenta de cobro TXT
│   └── documento_pdf.py    # Cuenta de cobro PDF (fpdf2)
├── app/
│   └── main.py             # App Streamlit
├── scripts/
│   └── calcular.py         # CLI
├── tests/
│   ├── test_retenciones.py # 30 tests originales
│   └── test_uvt_ica.py     # 23 tests nuevos (UVT, ICA, PDF)
├── examples/
│   ├── ejemplo_basico.py
│   ├── ejemplo_honorarios_alto_valor.py
│   ├── ejemplo_servicios_empresa.py
│   └── ejemplo_arrendamiento.py
├── data/
│   └── uvt_history.json    # UVT 2015–2025 (DIAN)
├── Makefile
└── requirements-app.txt
```

---

## Comandos Make

```bash
make run-app       # Lanza la app Streamlit
make run-tests     # pytest -v
make test          # pytest -q
make calcular      # Muestra --help del CLI
make instalar-app  # Instala requirements-app.txt
make ejemplo       # Cálculo rápido honorarios $3M
make tipos         # Tabla de tipos de servicio
```

---

## Marco legal

- **Art. 392 E.T.** — Retención en honorarios y servicios
- **Art. 401 E.T.** — Retención en arrendamiento y compras
- **Decreto 2418 de 2013** — Tarifas de retención
- **Ley 1607 de 2012, Art. 26** — IBC para independientes (40%)
- **Decreto 1601 de 2022** — Reglamentación SGSS independientes
- **Ley 14 de 1983, Art. 33** — ICA municipal
- **Art. 868 E.T.** — UVT (Unidad de Valor Tributario)
- **Circular UGPP 01/2023** — Aportes para arrendadores pasivos

---

## Tests

```bash
make run-tests
# 53 passed in ~1.5s
```

---

## Licencia

[MIT](LICENSE) © Brausin
