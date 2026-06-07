# 🧾 factura-co

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/Brausin/factura-co/actions/workflows/ci.yml/badge.svg)](https://github.com/Brausin/factura-co/actions)
[![Version](https://img.shields.io/badge/version-0.3.0-orange)](https://github.com/Brausin/factura-co)

**¿Sabes cuánto te van a descontar de tu próxima factura?**

Como freelancer o independiente en Colombia, cuando facturas $5.000.000 **no recibes $5.000.000**.
Tu cliente retiene el 11%, tú pagas salud y pensión, y al final te quedan $3.880.000. O menos.

`factura-co` calcula exactamente cuánto, por qué, y cómo planearlo — en una línea de Python o con una app web.

---

## ¿Para quién es?

- **Desarrolladores y diseñadores** que facturan honorarios a empresas
- **Consultores y asesores** con contratos por prestación de servicios
- **Abogados, médicos y arquitectos** en ejercicio independiente
- **Cualquier independiente** que quiera entender su ingreso neto real antes de negociar un precio

---

## Demo rápido

```
Factura: $5.000.000 — Honorarios — No declarante — Bogotá

  Valor bruto            $5.000.000
  Retención fuente (11%)  -$550.000
  IBC (40% del bruto)    $2.000.000
  Aporte salud (12.5%)    -$250.000
  Aporte pensión (16%)    -$320.000
  ─────────────────────────────────
  NETO A RECIBIR         $3.880.000  (77.6%)
```

---

## Casos de uso reales

### 💻 Desarrollador web — $5.000.000 en honorarios

Juan factura $5.000.000 a una empresa por desarrollo de un módulo. No es declarante de renta.

```python
from factura_co.calculadora import calcular_neto

r = calcular_neto(5_000_000, "honorarios")
print(f"Neto: ${r['neto']:,.0f}")    # $3.880.000
print(f"Retención: ${r['valor_retenido']:,.0f}")   # $550.000
```

**CLI:**
```bash
python scripts/calcular.py --valor 5000000 --tipo honorarios
```

---

### 🎨 Diseñadora — $1.800.000 en servicios (debajo del umbral)

Laura factura $1.800.000 por servicios de diseño. ¿Aplica retención?

```python
r = calcular_neto(1_800_000, "servicios")
# Servicios tienen umbral mínimo de 4 UVT (~$199.196 en 2025)
# Si el valor supera el umbral, aplica retención del 6%
```

El umbral se calcula automáticamente según el UVT vigente del año.

---

### ⚖️ Abogado — $15.000.000, declarante de renta

Carlos factura $15.000.000 en honorarios. Sus ingresos anuales superan 1.400 UVT — es declarante.

```python
r = calcular_neto(15_000_000, "honorarios", es_declarante=True)
# Tarifa baja de 11% a 10%: ahorra $150.000 en retención
print(f"Neto: ${r['neto']:,.0f}")    # $10.200.000
```

---

## Tres formas de usar

### 1. App web (recomendada)

```bash
git clone https://github.com/Brausin/factura-co.git
cd factura-co
pip install -r requirements-app.txt
streamlit run app/main.py
```

La app incluye:
- Calculadora con selector de tipo de servicio y descripción de cada uno
- Desglose visual con explicaciones inline de cada descuento
- **Calculadora inversa**: ingresa cuánto quieres recibir y calcula el bruto a facturar
- Casos de uso reales con números concretos
- Sección educativa: glosario, historial UVT, explicación de cada retención
- Generador de cuenta de cobro en PDF y TXT

---

### 2. CLI — desde la terminal

```bash
pip install -e .
pip install -r requirements-app.txt

# Cálculo básico
python scripts/calcular.py --valor 3000000 --tipo honorarios

# Declarante de renta (tarifa 10% en lugar de 11%)
python scripts/calcular.py --valor 8000000 --tipo honorarios --declarante

# Exportar resultado a JSON
python scripts/calcular.py --valor 5000000 --exportar

# Ver todos los tipos de servicio disponibles
python scripts/calcular.py --listar-tipos
```

**Ejemplo de salida:**

```
Valor factura:   $3.000.000
Tipo servicio:   honorarios (no declarante)
Retención (11%): -$330.000
IBC (40%):       $1.200.000
Salud (12.5%):   -$150.000
Pensión (16%):   -$192.000
─────────────────────────────
NETO:            $2.328.000  (77.6%)
```

---

### 3. Librería Python

```bash
pip install -e .
```

```python
from factura_co.calculadora import calcular_neto, generar_resumen
from factura_co.retenciones import obtener_uvt, calcular_ica

# Cálculo completo
resultado = calcular_neto(5_000_000, "honorarios")
generar_resumen(resultado)

# Solo retención, sin aportes
ret = calcular_neto(5_000_000, "honorarios", incluir_aportes=False)

# Calcular ReteICA para Bogotá
ica = calcular_ica(5_000_000, "bogota", "servicios_profesionales")
print(f"ReteICA: ${ica['valor_ica']:,}")  # $48.300

# Consultar UVT por año
print(obtener_uvt(2024))   # 47065
print(obtener_uvt(2025))   # 49799
print(obtener_uvt())       # año más reciente
```

---

## Instalación completa

```bash
git clone https://github.com/Brausin/factura-co.git
cd factura-co

# Solo librería y CLI
pip install -e .

# Librería + app web + CLI
pip install -r requirements-app.txt
```

**Requisitos**: Python 3.8+

---

## Estructura del proyecto

```
factura-co/
├── app/
│   └── main.py              # App Streamlit (5 secciones)
├── src/factura_co/
│   ├── calculadora.py       # calcular_neto(), generar_resumen()
│   ├── retenciones.py       # calcular_retencion(), calcular_ica(), UVT
│   ├── aportes.py           # calcular_aportes(), IBC
│   └── documento.py         # generar_documento_txt()
├── data/
│   ├── uvt_history.json     # UVT 2015–2025 con resoluciones DIAN
│   └── tablas_retencion_2025.json  # Tablas completas de retención 2025
├── scripts/
│   ├── calcular.py          # CLI principal
│   └── actualizar_uvt.py   # Actualiza uvt_history.json cada año
├── examples/
│   ├── ejemplo_basico.py
│   ├── ejemplo_honorarios_alto_valor.py
│   ├── ejemplo_servicios_empresa.py
│   └── ejemplo_arrendamiento.py
├── tests/
│   ├── test_retenciones.py
│   └── test_documento.py
└── .github/workflows/
    ├── ci.yml               # Tests en cada push
    └── actualizar_tablas.yml  # Actualización anual UVT (1 ene)
```

---

## Marco legal

| Concepto | Fuente |
|---|---|
| Retención en honorarios (11% / 10%) | Art. 392 E.T. |
| Retención en servicios (6% / 4%) | Art. 392 E.T. |
| Retención en arrendamiento (3.5%) | Art. 401 E.T. |
| IBC independientes (40% ingreso bruto) | Art. 18 Ley 100/1993, Decreto 1601/2022 |
| Salud independientes (12.5% IBC) | Art. 204 Ley 100/1993 |
| Pensión independientes (16% IBC) | Art. 18 Ley 100/1993 |
| UVT 2025 = $49.799 | Resolución DIAN 000186 de 2024 |
| ICA Bogotá — servicios profesionales (9.66‰) | Acuerdo 65 de 2002, Concejo de Bogotá |

---

## Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Contribuir

1. Fork del repositorio
2. Crea tu rama: `git checkout -b feat/nueva-funcionalidad`
3. Commit con mensaje descriptivo
4. Pull request con descripción del cambio y fuente normativa si aplica

Para agregar el UVT de un nuevo año: edita `UVT_VALORES_CONOCIDOS` en `scripts/actualizar_uvt.py`
con el valor oficial de la resolución DIAN correspondiente.

---

## Licencia

MIT — ver [LICENSE](LICENSE)

---

> `factura-co` es una herramienta de orientación. Para decisiones fiscales concretas, consulta un contador público certificado.

---

## v0.3.0 — Suite financiera completa para freelancers internacionales

### Nuevas funcionalidades

#### 💱 Comparador de plataformas de pago internacional

Resuelve la pregunta clave: **si me pagan $1.000 USD, ¿cuánto llega a mi cuenta?**

```python
from factura_co.comparador import comparar_plataformas, tabla_comparacion

# Comparar todas las opciones para $1.000 USD a TRM de $4.200
tabla = tabla_comparacion(1000, 4200)
print(tabla)
# #1  Wise            $995.90  -$4.10   $4,155,432  0.4%  ✓ mejor
# #2  Payoneer        $980.00  -$20.00  $4,017,600  2.5%  (-$137,832)
# #3  Binance P2P     $999.00  -$1.00   $4,154,580  1.1%  (-$852)
# ...
```

Plataformas cubiertas: **PayPal, Wise, Payoneer, Upwork (escalonado), Freelancer, Binance P2P, Buda.com, SWIFT, Nequi Internacional**

#### 📈 Proyección anual de ingresos

```python
from factura_co.proyeccion import proyeccion_anual, proyeccion_desde_usd

# Proyección desde COP
proy = proyeccion_anual(5_000_000, tipo_servicio="honorarios")
print(f"Neto anual: ${proy['neto_anual']:,.0f} COP")
print(f"Promedio mensual real: ${proy['neto_mensual_promedio']:,.0f} COP")

# Proyección desde USD con plataforma
proy_usd = proyeccion_desde_usd(1000, trm=4200, plataforma="wise")
```

#### 🔄 Calculadora inversa extendida con plataformas

```python
from factura_co.calculadora import calcular_bruto_necesario

# ¿Cuánto debe pagarte el cliente para que TÚ recibas $3M netos?
r = calcular_bruto_necesario(
    neto_cop_deseado=3_000_000,
    plataforma="wise",
    trm=4200
)
print(f"Bruto necesario en COP: ${r['bruto_necesario']:,.0f}")
print(f"El cliente debe enviarte: ${r['bruto_usd_necesario']:,.2f} USD")
```

#### 🌐 TRM en tiempo real

```python
from factura_co.trm_live import get_trm_hoy, get_trm_info

trm = get_trm_hoy()   # Con 3 fuentes de fallback
info = get_trm_info() # Incluye fuente y si es estimado
```

### Tests: 121 pasando

```bash
$ python -m pytest tests/ -q
121 passed in 1.33s
```

