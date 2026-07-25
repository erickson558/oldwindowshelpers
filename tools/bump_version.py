"""Sube la versión de la app (SemVer) y prepara una entrada en CHANGELOG.md.

Uso:
    python tools/bump_version.py patch   # 0.1.0 -> 0.1.1 (fixes)
    python tools/bump_version.py minor   # 0.1.0 -> 0.2.0 (features nuevas)
    python tools/bump_version.py major   # 0.1.0 -> 1.0.0 (cambios incompatibles)

No hace commit ni tag por sí solo — eso lo orquesta el skill /release (o vos a
mano con los comandos que este script te deja impresos al final). Acá solo se
actualizan los archivos:
  1. version.py       (fuente única de verdad, la lee toda la app)
  2. CHANGELOG.md      (se agrega una sección nueva arriba, lista para editar)
"""

import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_ROOT / "version.py"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

BUMP_TYPES = ("major", "minor", "patch")


def read_version() -> tuple[int, int, int]:
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not match:
        raise ValueError(f"No se encontro __version__ en {VERSION_FILE}")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def write_version(new_version: str) -> None:
    text = VERSION_FILE.read_text(encoding="utf-8")
    text = re.sub(r'__version__\s*=\s*"\d+\.\d+\.\d+"', f'__version__ = "{new_version}"', text)
    VERSION_FILE.write_text(text, encoding="utf-8")


def bump(current: tuple[int, int, int], bump_type: str) -> str:
    major, minor, patch = current
    if bump_type == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump_type == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def update_changelog(new_version: str) -> None:
    entry = f"## [{new_version}] - {date.today().isoformat()}\n\n- \n\n"
    if CHANGELOG_FILE.exists():
        existing = CHANGELOG_FILE.read_text(encoding="utf-8")
    else:
        existing = (
            "# Changelog\n\n"
            "Todos los cambios notables de este proyecto se documentan acá.\n"
            "Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) "
            "y este proyecto sigue [SemVer](https://semver.org/lang/es/).\n\n"
        )
    if "## [" in existing:
        idx = existing.index("## [")
        existing = existing[:idx] + entry + existing[idx:]
    else:
        existing = existing.rstrip() + "\n\n" + entry
    CHANGELOG_FILE.write_text(existing, encoding="utf-8")


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in BUMP_TYPES:
        print(f"Uso: python tools/bump_version.py <{'|'.join(BUMP_TYPES)}>")
        return 1

    bump_type = argv[0]
    current = read_version()
    new_version = bump(current, bump_type)
    write_version(new_version)
    update_changelog(new_version)

    current_str = ".".join(map(str, current))
    print(f"Version: {current_str} -> {new_version}")
    print(f"CHANGELOG.md: completa el detalle del cambio bajo '## [{new_version}]'")
    print()
    print("Proximos pasos sugeridos:")
    print("  git add version.py CHANGELOG.md")
    print(f'  git commit -m "chore(release): v{new_version}"')
    print(f'  git tag -a v{new_version} -m "v{new_version}"')
    print("  git push origin main --tags")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
