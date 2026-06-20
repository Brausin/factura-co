"""Tests dorados (snapshot) para los generadores de PDF.

Estrategia: se eliminan los campos de fecha volátiles del PDF
(/CreationDate, /ModDate) con regex antes de comparar bytes.
Esto hace la comparación determinista en cualquier máquina y momento.

Los hashes de referencia se almacenan en tests/golden/hashes.json.

Para regenerar los hashes (tras un cambio intencional de diseño):
    REGEN_GOLDEN=1 pytest tests/test_pdf_golden.py -v
"""

import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

import pytest

from factura_co.documento_pdf import generar_pdf
from factura_co.factura_pdf import generar_factura

_GOLDEN_DIR = Path(__file__).parent / "golden"
_HASHES_FILE = _GOLDEN_DIR / "hashes.json"

# Campos que fpdf2 genera con valores aleatorios o temporales en cada proceso.
# /CreationDate, /ModDate: marcas de tiempo.
# /ID [...]: identificador único del documento (UUID hexadecimal).
_RE_VOLATILE = re.compile(
    rb"/(?:CreationDate|ModDate)\s*\([^)]*\)"
    rb"|/ID\s*\[<[0-9A-Fa-f]*><[0-9A-Fa-f]*>\]"
)


def _normalizar(pdf_bytes: bytes) -> bytes:
    """Elimina campos volátiles del PDF para comparación determinista."""
    return _RE_VOLATILE.sub(b"", pdf_bytes)


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


_FREELANCER = {
    "nombre": "Ana García",
    "cedula": "52.123.456-7",
    "ciudad": "Bogotá",
    "email": "ana@ejemplo.co",
    "banco": "Bancolombia",
    "cuenta": "123-456789-00",
    "tipo_cuenta": "Ahorros",
}
_CLIENTE = {"empresa": "Tech Corp SAS", "nit": "900.123.456-7"}

# Cada caso es un callable sin argumentos que produce bytes del PDF.
_CASOS: dict[str, object] = {
    "factura_minima": lambda: generar_factura({
        "nombre_freelancer": "Ana García",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": "Desarrollo de API — Sprint Golden",
        "valor_cop": 5_000_000,
        "retencion_pct": 11,
        "fecha": "2026-01-15",
        "numero_factura": "FV-GOLDEN-001",
    }),
    "factura_completa": lambda: generar_factura({
        "nombre_freelancer": "Ana García",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": "Desarrollo de API — Sprint Golden",
        "valor_cop": 5_000_000,
        "retencion_pct": 11,
        "fecha": "2026-01-15",
        "numero_factura": "FV-GOLDEN-002",
        "ciudad": "Bogotá",
        "email": "ana@ejemplo.co",
        "telefono": "300 123 4567",
        "forma_de_pago": "Transferencia bancaria",
        "banco": "Bancolombia",
        "cuenta": "123-456789-00",
        "tipo_cuenta": "Ahorros",
        "notas": "Pago a 15 días.",
    }),
    "factura_items_multiples": lambda: generar_factura({
        "nombre_freelancer": "Ana García",
        "nit_freelancer": "52.123.456-7",
        "nombre_cliente": "Tech Corp SAS",
        "nit_cliente": "900.123.456-7",
        "descripcion_servicio": "Multi-ítem",
        "valor_cop": 5_000_000,
        "items": [("Diseño UX", 2_000_000), ("Implementación backend", 3_000_000)],
        "retencion_pct": 11,
        "fecha": "2026-01-15",
        "numero_factura": "FV-GOLDEN-003",
    }),
    "cuenta_cobro_minima": lambda: generar_pdf(
        _FREELANCER,
        _CLIENTE,
        5_000_000,
        "Consultoría digital — Sprint Golden",
        numero="CC-GOLDEN-001",
        fecha=date(2026, 1, 15),
        incluir_retencion=False,
    ),
    "cuenta_cobro_con_retenciones": lambda: generar_pdf(
        _FREELANCER,
        _CLIENTE,
        5_000_000,
        "Consultoría digital — Sprint Golden",
        numero="CC-GOLDEN-002",
        fecha=date(2026, 1, 15),
        incluir_retencion=True,
        tarifa_retencion=0.11,
        incluir_ica=True,
        valor_ica=30_000,
    ),
}


def _cargar_hashes() -> dict:
    if _HASHES_FILE.exists():
        return json.loads(_HASHES_FILE.read_text(encoding="utf-8"))
    return {}


def _guardar_hashes(hashes: dict) -> None:
    _GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    _HASHES_FILE.write_text(
        json.dumps(hashes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("nombre", sorted(_CASOS))
def test_pdf_golden(nombre):
    """Verifica que el PDF generado coincide con el hash de referencia.

    Con REGEN_GOLDEN=1 regenera los hashes en lugar de comparar.
    """
    pdf_bytes = _CASOS[nombre]()
    assert pdf_bytes[:4] == b"%PDF", f"{nombre}: los bytes no son un PDF válido"

    normalizado = _normalizar(pdf_bytes)
    hash_actual = _sha256(normalizado)

    if os.environ.get("REGEN_GOLDEN") == "1":
        hashes = _cargar_hashes()
        hashes[nombre] = hash_actual
        _guardar_hashes(hashes)
        return  # pasa siempre en modo regen

    hashes = _cargar_hashes()
    assert nombre in hashes, (
        f"No hay hash golden para '{nombre}'. "
        f"Ejecuta: REGEN_GOLDEN=1 pytest tests/test_pdf_golden.py -v"
    )
    assert hash_actual == hashes[nombre], (
        f"El PDF '{nombre}' cambió visualmente.\n"
        f"  Esperado : {hashes[nombre]}\n"
        f"  Actual   : {hash_actual}\n"
        f"Si el cambio es intencional, regenera: "
        f"REGEN_GOLDEN=1 pytest tests/test_pdf_golden.py -v"
    )
