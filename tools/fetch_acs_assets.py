"""Descarga y convierte, con la MISMA fidelidad que los 6 personajes
originales (animaciones completas y nombradas: Wave, Greeting, Congratulate,
etc.), los personajes para los que se consiguió su archivo .acs real y
verificado: Mother Nature, Office Logo y The Dot.

A diferencia de tools/fetch_extra_assets.py (que generaba estos mismos
personajes con una única animación "Idle", por no tener forma de decodificar
el binario original), este script usa tools/acs_decoder.py — un decodificador
propio del formato Microsoft Agent (.acs), verificado contra tres archivos
reales al 100% de éxito (ver specs/SPEC.md 2.3c). Reemplaza por completo los
assets de esos 3 personajes generados por fetch_extra_assets.py.

Uso:
    python tools/fetch_acs_assets.py
"""

import sys
import urllib.request
from pathlib import Path

import acs_decoder  # módulo hermano en tools/ (no es un paquete con __init__.py)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "agents"

# Los tres .acs reales que investigamos y confirmamos (ver specs/SPEC.md 2.1):
# vienen del mismo archivo de preservación "Binder 97" en archive.org que ya
# citamos en NOTICE para el resto de los personajes.
ACS_SOURCES = {
    "MotherNature": "https://archive.org/download/binder-97-office972000assistants/MNATURE.ACS",
    "OfficeLogo": "https://archive.org/download/binder-97-office972000assistants/LOGO.ACS",
    "Dot": "https://archive.org/download/binder-97-office972000assistants/DOT.ACS",
}


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def convert_character(name: str, acs_bytes: bytes) -> None:
    dest = ASSETS_DIR / name
    dest.mkdir(parents=True, exist_ok=True)
    source_path = dest / "_source.acs"
    source_path.write_bytes(acs_bytes)
    try:
        character = acs_decoder.parse_acs_file(str(source_path))
    finally:
        source_path.unlink(missing_ok=True)  # no lo dejamos en el repo, solo nos sirvió para parsear

    stats = acs_decoder.build_agent_assets(character, name, dest)
    print(
        f"  OK: {name} -> {stats['animation_count']} animaciones, {stats['frame_count']} frames, "
        f"{stats['unique_images']} imagenes unicas en el sheet"
    )


def main(argv: list[str]) -> int:
    names = argv or list(ACS_SOURCES.keys())
    failures = []
    for name in names:
        url = ACS_SOURCES.get(name)
        if url is None:
            print(f"  {name}: no tengo una fuente .acs conocida para este personaje")
            failures.append(name)
            continue
        print(f"Descargando {name} desde {url} ...")
        try:
            raw = _download(url)
            convert_character(name, raw)
        except Exception as exc:  # noqa: BLE001 - seguimos con el resto si uno falla
            failures.append(name)
            print(f"  FALLO {name}: {exc}")

    if failures:
        print(f"\nNo se pudieron convertir: {', '.join(failures)}.")
        return 1

    print(f"\nListo. Personajes de alta fidelidad (via .acs) en {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
