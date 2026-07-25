"""Importador EXPERIMENTAL de personajes desde archivos .acs (Microsoft Agent
Character File) de tu propia instalación/medio de instalación de Office.

Por qué es experimental: .acs es un formato binario propietario de los años
90, mal documentado públicamente (compresión propia + estructuras internas de
Microsoft Agent). No existe hoy un parser Python de referencia confiable, y
reconstruirlo por completo excede el alcance de la v0.1.0 de este proyecto.

Qué hace esta versión: detecta si un archivo es un .acs válido (firma/cabecera)
e informa metadata básica, pero NO extrae el sprite sheet ni las animaciones.
Si vos (o la comunidad) consiguen o escriben un parser real, este es el punto
de extensión: `import_acs()` debería terminar generando la misma carpeta
assets/agents/<Nombre>/{agent.json,map.png} que produce tools/fetch_assets.py
(mismo esquema, documentado en app/animation.py), para que el resto de la app
no necesite cambiar nada.

Uso actual:
    python tools/acs_importer.py "C:\\ruta\\a\\CLIPPIT.ACS"
"""

import sys
from pathlib import Path

# Los .acs empiezan con esta firma de 4 bytes (formato RIFF-like usado por
# Microsoft Agent); nos sirve para dar un diagnóstico honesto en vez de nada.
ACS_MAGIC = b"\x14\x00\x00\x00"


def inspect_acs(path: Path) -> dict:
    data = path.read_bytes()
    looks_like_acs = data[:4] == ACS_MAGIC
    return {
        "path": str(path),
        "size_bytes": len(data),
        "looks_like_acs": looks_like_acs,
    }


def import_acs(path: Path) -> None:
    info = inspect_acs(path)
    print(f"Archivo: {info['path']} ({info['size_bytes']} bytes)")
    if not info["looks_like_acs"]:
        print("No parece un archivo .acs válido (firma de cabecera no coincide).")
        return

    print(
        "Se detectó un .acs válido, pero este importador todavía no sabe "
        "decodificar su sprite sheet ni sus animaciones (ver docstring de este "
        "archivo). Por ahora, para agregar un personaje nuevo usá "
        "tools/fetch_assets.py, o armá a mano una carpeta "
        "assets/agents/<Nombre>/ con agent.json + map.png siguiendo el esquema "
        "de app/animation.py."
    )


def main(argv: list[str]) -> int:
    if not argv:
        print("Uso: python tools/acs_importer.py <archivo.acs>")
        return 1
    import_acs(Path(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
