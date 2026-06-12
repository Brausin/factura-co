# Mejoras — factura-co

## Archivos NUEVOS
| Archivo | Qué hace |
|---|---|
| `src/factura_co/cli.py` | CLI completo (`factura-co neto/bruto/comparar/trm/tipos`, con `--json`). **Arregla el bug crítico**: `setup.py` declaraba el comando `factura-co=factura_co.calculadora:main`, pero `calculadora.py` no tiene función `main` → el comando instalado estaba roto. |
| `.github/workflows/ci.yml` | CI real en GitHub Actions: pytest en Python 3.10/3.11/3.12 + verificación del CLI. El badge de tests del README ahora tendrá respaldo automático. |
| `.github/dependabot.yml` | Actualizaciones automáticas mensuales de dependencias pip y actions. |

## Archivos MODIFICADOS (reemplazar los existentes)
| Archivo | Cambio |
|---|---|
| `setup.py` | 1) `entry_points` apunta al nuevo `factura_co.cli:main` (antes roto). 2) Versión `0.2.0 → 0.3.0` para coincidir con `__init__.py`. 3) `python_requires ">=3.8" → ">=3.10"`: el código usa sintaxis `float \| None` que NO funciona en 3.8/3.9 — antes pip permitía instalar en versiones donde el paquete crashea. 4) Classifiers de versión explícitos. |
| `src/factura_co/trm_live.py` | Valor de respaldo actualizado: `4150 (2025-01-15) → 4340 (2026-06-01)`, consistente con la serie histórica de tu repo colombia-data-insights. |

## Detectado pero NO tocado (decide tú)
- Docstring de `calcular_neto()` en `calculadora.py`: el ejemplo dice que el neto de $3.000.000 es `1957500 (65.25%)`, pero el código real (correcto) devuelve `2299500 (76.65%)`. El ejemplo está desactualizado; corrígelo cuando quieras.
- `proyeccion.py` usa `UVT_2024` fijo aunque `retenciones.py` ya carga `uvt_history.json`. Unificarlo cambiaría resultados numéricos (y posiblemente tus 145 tests), por eso no lo cambié.

## Verificación realizada
- `cli.py` y `trm_live.py` compilados y probados contra los módulos reales del repo:
  - `neto 3000000` → $2.299.500 (76.7%) ✔
  - `bruto 3000000` → facturar $3.865.980 ✔ (inverso exacto)
  - `comparar 1000 --trm 4200` → ranking correcto, Wise primero ✔
  - manejo de errores y `--json` ✔

---

# Mejoras de UI (revisión con la skill ui-ux-pro-max)

La app ya tenía un design system de la skill (Glassmorphism oro/violeta).
El nuevo análisis para "fintech / personal finance" mantiene el vidrio y el
oro, pero marca los **gradientes morados "AI" como anti-patrón fintech** y
recomienda semántica de dinero: el CTA pasó de violeta a **esmeralda
`#10B981`**. Recomendación completa en `design-system/factura-co/MASTER.md`.

## Archivos MODIFICADOS
| Archivo | Cambio |
|---|---|
| `app/ui.py` | CTA, foco de inputs, radio segmentado y hover del sidebar pasan de violeta a esmeralda (el violeta queda solo como tinte tenue del mesh de fondo). Texto del botón en `#04221A` sobre esmeralda (6.6:1). Plotly: `separators=",."` para formato es-CO también dentro de los gráficos (antes `4.450.000` en tarjetas pero `4,450,000` en ejes/hover), etiquetas de barras con `fmt_cop` y `cliponaxis=False` (ya no se cortan), donut con más aire para la leyenda. CSS nuevo para `st.code` (vidrio oscuro), alertas nativas y valor del slider en tabular-nums. |
| `app/main.py` | **Bugs corregidos**: (1) `US$ {valor:,}` mostraba `US$ 1,000.0` → ahora `ui.fmt_usd()` en el resumen para compartir, el subtítulo del comparador y la proyección USD; (2) defaults de TRM acotados con `_trm_default()` — si la TRM en vivo saliera del rango [2.000, 8.000] el `number_input` crasheaba; (3) guardas con error claro en español si `comparar_plataformas` no devuelve filas o si `calcular_neto_plataforma` / `calcular_bruto_necesario` lanzan `ValueError`; (4) el Inicio degrada con tarjeta «—» si el cálculo de mejor plataforma falla, en vez de tumbar la página; (5) slider de meses del modo COP con `key` propio (antes compartía estado a medias con el del modo USD); (6) nombre del CSV exportado sin decimales (`usd1000` y no `usd1000.0`); (7) spinners «Generando…» en los dos generadores de PDF. |

## Archivos NUEVOS
| Archivo | Qué hace |
|---|---|
| `.streamlit/config.toml` | Tema base oscuro + `primaryColor` esmeralda: los widgets nativos (toggle, slider, radio, date picker) dejan de salir con el rojo claro por defecto de Streamlit. |
| `design-system/factura-co/MASTER.md` | Salida íntegra de la skill para "fintech freelancer payments" (paleta trust blue + profit green, IBM Plex Sans, anti-patrones). Aplicada de forma selectiva para no romper la identidad ya construida; si algún día quieres la versión completa, ahí está documentada. |

## Verificación de UI realizada
- 15 escenarios sobre un doble de pruebas estricto de Streamlit + pandas real:
  las 7 páginas, Upwork con tramos, proyección USD, factura y cuenta de cobro
  generadas (bytes de PDF validados en `download_button`), valor 0, campos
  vacíos y calculadora con plataforma. ✔
- Checklist de la skill: sin emojis como iconos ✔ · contraste ≥4.5:1 en pares
  texto/fondo y botón/CTA (6.6–17.1:1) ✔ · focus visible ✔ ·
  `prefers-reduced-motion` ✔ · sin saltos de layout en hover ✔.
- Nota: el sandbox no permite instalar Streamlit real (sin red a PyPI);
  recomendado un `streamlit run app/main.py` local como humo final.
