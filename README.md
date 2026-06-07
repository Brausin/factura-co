# 🧾 factura-co

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Brausin/factura-co?style=social)](https://github.com/Brausin/factura-co)
[![Tests](https://github.com/Brausin/factura-co/actions/workflows/ci.yml/badge.svg)](https://github.com/Brausin/factura-co/actions)

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

Dado el valor de una factura, `factura-co` calcula automáticamente:

| Concepto | Ejemplo ($3.000.000 en honorarios) |
|---|---|
| Valor bruto | $3.000.000 |
| Retención en la fuente (11%) | -$330.000 |
| Base cotización (40%) | $1.200.000 |
| Aporte salud (12.5%) | -$150.000 |
| Aporte pensión (16%) | -$192.000 |
| **Ingreso neto real** | **$2.328.000** |

```python
from factura_co.calculadora import calcular_neto, generar_resumen

resultado = calcular_neto(3_000_000, "honorarios")
generar_resumen(resultado)
```

```
============================================================
        DESGLOSE DE INGRESO - factura-co
============================================================
  Valor factura:              $3,000,000
  Retención (11.0%):           -$330,000
  Valor a recibir:            $2,670,000

  Base cotización (40%):      $1,200,000
  Aporte salud (12.5%):        -$150,000
  Aporte pensión (16.0%):      -$192,000
  Total aportes:               -$342,000

  ──────────────────────────────────────
  INGRESO NETO REAL:          $2,328,000
============================================================
```

---

## Instalación y uso rápido

### Requisitos

- Python 3.8+
- pip

### Instalación

```bash
git clone https://github.com/Brausin/factura-co.git
cd factura-co
pip install -r requirements.txt
pip install -e .
```

### Uso como librería

```python
from factura_co.calculadora import calcular_neto

# Honorarios profesionales
resultado = calcular_neto(5_000_000, "honorarios")
print(f"Neto: ${resultado['neto']:,.0f}")

# Servicio técnico con aportes
resultado = calcular_neto(2_000_000, "servicios", incluir_aportes=True)
print(resultado)
```

### Uso desde línea de comandos

```bash
python scripts/calcular.py --valor 3000000 --tipo honorarios
python scripts/calcular.py --valor 1500000 --tipo servicios
python scripts/calcular.py --valor 4000000 --tipo honorarios --sin-aportes
```

### Generar documento de cobro

```python
from factura_co.documento import generar_documento_txt

datos_freelancer = {
    "nombre": "Ana García",
    "cedula": "1234567890",
    "banco": "Bancolombia",
    "cuenta": "123-456789-00",
    "ciudad": "Bogotá"
}

datos_cliente = {
    "empresa": "Tech Corp SAS",
    "nit": "900.123.456-7",
    "contacto": "Carlos Martínez"
}

doc = generar_documento_txt(
    datos_freelancer,
    datos_cliente,
    valor=3_000_000,
    descripcion="Desarrollo de módulo de autenticación para plataforma web"
)
print(doc)
```

---

## Tipos de servicio soportados

| Tipo | Tasa retención | Descripción |
|---|---|---|
| `honorarios` | 10% / 11% | Servicios profesionales y técnicos |
| `servicios` | 4% / 6% | Servicios en general |
| `arrendamiento` | 3.5% | Arrendamiento de bienes muebles |
| `compras` | 2.5% / 3.5% | Compras generales |
| `transporte` | 3.5% | Servicios de transporte |

> **Nota:** La tasa varía según si el beneficiario es declarante de renta. Por defecto se aplica la tasa para **no declarantes** (más conservadora).

---

## Casos de uso

### Diseñador freelance
```python
# Proyecto de branding: $4.500.000
resultado = calcular_neto(4_500_000, "honorarios")
# Neto real después de retención y aportes: ~$3.492.000
```

### Desarrollador independiente
```python
# Sprint de desarrollo: $6.000.000
resultado = calcular_neto(6_000_000, "honorarios")
# Neto real: ~$4.656.000
```

### Consultor de negocios
```python
# Consultoría mensual: $8.000.000
resultado = calcular_neto(8_000_000, "honorarios")
# Neto real: ~$6.208.000
```

---

## Roadmap

- [x] **v0.1** — Calculadora CLI con retenciones y aportes 2024
- [x] **v0.2** — Generador de documento de cobro en texto plano
- [ ] **v0.3** — Generador de cuenta de cobro en PDF (con logo)
- [ ] **v0.4** — Aplicación web con interfaz simple
- [ ] **v1.0** — Historial de facturas y exportación a Excel

---

## Contribuir

¿Encontraste un error en las tablas de retención? ¿Cambió una tasa en 2025? Los PRs son bienvenidos.

```bash
git clone https://github.com/Brausin/factura-co.git
cd factura-co
pip install -r requirements.txt
pytest tests/
```

---

## Licencia

MIT © [Brausin](https://github.com/Brausin)

Este proyecto no es asesoría tributaria. Para decisiones fiscales importantes, consulta a un contador.
