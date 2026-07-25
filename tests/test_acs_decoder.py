"""El descompresor de tools/acs_decoder.py se verificó "en serio" corriéndolo
contra 3 archivos .acs reales (3589 frames en total, 100% decodificados al
tamaño exacto esperado — ver specs/SPEC.md 2.3c). Acá solo dejamos un smoke
test rápido contra el ejemplo trabajado a mano que trae el spec de Lebeau,
para detectar una regresión futura sin tener que descargar nada de internet."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from acs_decoder import decompress  # noqa: E402


def test_decompress_worked_example_from_spec():
    # "00 40 00 04 10 D0 90 80 42 ED 98 01 B7 FF FF FF FF FF FF" del spec de
    # Lebeau Software: arranca con dos literales (0x20, 0x00) seguidos de
    # referencias hacia atrás.
    hex_bytes = "00 40 00 04 10 D0 90 80 42 ED 98 01 B7 FF FF FF FF FF FF"
    stream = bytes.fromhex(hex_bytes.replace(" ", ""))
    out = decompress(stream, expected_size=32)
    assert out[:2] == b"\x20\x00"
    assert len(out) == 32
