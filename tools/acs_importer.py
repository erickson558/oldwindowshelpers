"""Importador de personajes desde archivos .acs (Microsoft Agent Character
File) propios — por ejemplo, de una instalación o medio de instalación de
Office que todavía tengas guardado.

Antes esta herramienta era experimental: solo detectaba si un archivo era un
.acs válido, sin poder leer su sprite sheet ni sus animaciones (el formato
parecía demasiado opaco para reverse-engineerlo a ciegas). Se investigó en
serio — ver tools/acs_decoder.py y specs/SPEC.md 2.3c — y ahora sí puede
convertir un .acs real a un personaje completo, con la misma fidelidad que
el resto del roster (animaciones nombradas: Wave, Greeting, Congratulate,
etc., no una sola animación "Idle").

Uso:
    python tools/acs_importer.py "C:\\ruta\\a\\CLIPPIT.ACS" NombrePersonaje

Si no le das un nombre, usa el nombre del archivo (sin extensión).
"""

import sys
from pathlib import Path

import acs_decoder  # módulo hermano en tools/ (no es un paquete con __init__.py)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "agents"


def import_acs(path: Path, name: str) -> None:
    print(f"Archivo: {path} ({path.stat().st_size} bytes)")
    try:
        character = acs_decoder.parse_acs_file(str(path))
    except acs_decoder.AcsParseError as exc:
        print(f"No se pudo leer como .acs de Microsoft Agent: {exc}")
        return
    except Exception as exc:  # noqa: BLE001 - queremos un mensaje claro, no un traceback crudo
        print(f"Error inesperado decodificando el archivo: {exc}")
        print(
            "Si el archivo es válido pero esto falla, puede que use una "
            "característica no cubierta (ver limitaciones en specs/SPEC.md "
            "2.3c, ej. el bloque TTS) — revisá tools/acs_decoder.py."
        )
        return

    dest = ASSETS_DIR / name
    stats = acs_decoder.build_agent_assets(character, name, dest)
    print(
        f"OK: {name} -> {stats['animation_count']} animaciones, {stats['frame_count']} frames "
        f"({stats['unique_images']} imagenes unicas) en {dest}"
    )
    print("Reiniciá la app (o corré python -m pytest tests/ -v) para verlo en el selector de personajes.")


def main(argv: list[str]) -> int:
    if not argv:
        print('Uso: python tools/acs_importer.py "C:\\ruta\\a\\ARCHIVO.ACS" [NombrePersonaje]')
        return 1
    path = Path(argv[0])
    if not path.exists():
        print(f"No existe el archivo: {path}")
        return 1
    name = argv[1] if len(argv) > 1 else path.stem
    import_acs(path, name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
