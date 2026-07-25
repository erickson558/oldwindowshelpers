"""Compila main.py a un .exe standalone, sin consola, con el ícono local, y lo
deja en la raíz del proyecto (misma carpeta que main.py).

Uso:
    python tools/build_exe.py

Es exactamente lo que corre .github/workflows/release.yml en CI; este script
existe para poder compilar igual en tu propia máquina sin depender de GitHub.

Sobre falsos positivos de antivirus (Kaspersky y similares): un .exe armado
con PyInstaller y sin firmar (no tenemos un certificado de firma de código,
que cuesta dinero y no se puede automatizar acá) dispara heurísticas de
varios antivirus con bastante frecuencia — es un falso positivo muy conocido
y documentado en la comunidad de PyInstaller, no un indicio real de código
malicioso. Dos mitigaciones que sí podemos aplicar sin firmar el ejecutable:
  1. --noupx: UPX comprime el binario, pero ese mismo empaquetado lo usa
     muchísimo malware para evadir firmas — evitarlo baja bastante la tasa
     de falsos positivos.
  2. Un recurso de versión (--version-file) con metadata real (nombre de la
     empresa/producto, descripción, versión) — los binarios maliciosos
     casi nunca la tienen, y su ausencia es en sí misma una señal heurística
     que usan varios motores.
Ver specs/SPEC.md y README.md para más detalle y qué hacer si tu antivirus
igual lo bloquea (excepción puntual o reporte de falso positivo).
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from version import __version__  # noqa: E402  (requiere el sys.path.insert de arriba)

ICON = PROJECT_ROOT / "clippy_icon_136771.ico"
APP_NAME = "OldWindowsHelpers"
DATA_SEP = ";"  # PyInstaller en Windows separa src y destino de --add-data con ";"
BUILD_DIR = PROJECT_ROOT / "build"


def _version_tuple() -> tuple[int, int, int, int]:
    parts = [int(p) for p in __version__.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def _write_version_info() -> Path:
    """Genera el recurso de versión de Windows para el .exe (metadata visible
    en la pestaña "Detalles" de sus propiedades). Se regenera en cada build a
    partir de version.py para que nunca quede desactualizado."""
    vers = _version_tuple()
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={vers},
    prodvers={vers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'erickson558 (github.com/erickson558)'),
        StringStruct(u'FileDescription', u'Ayudantes de Office - asistentes clasicos flotantes'),
        StringStruct(u'FileVersion', u'{__version__}'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Codigo (c) 2026 erickson558, Apache License 2.0'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'OldWindowsHelpers'),
        StringStruct(u'ProductVersion', u'{__version__}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    path = BUILD_DIR / "version_info.txt"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    if not ICON.exists():
        print(f"No se encontró el ícono en {ICON}")
        return 1

    version_info_path = _write_version_info()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",  # es una app de escritorio: no debe abrir consola
        "--noupx",  # ver docstring: UPX dispara heuristicas de antivirus
        "--name",
        APP_NAME,
        "--icon",
        str(ICON),
        "--version-file",
        str(version_info_path),
        "--add-data",
        f"{PROJECT_ROOT / 'assets'}{DATA_SEP}assets",
        "--add-data",
        f"{PROJECT_ROOT / 'locales'}{DATA_SEP}locales",
        "--add-data",
        f"{ICON}{DATA_SEP}.",
        "--distpath",
        str(PROJECT_ROOT),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(BUILD_DIR),
        "--noconfirm",
        str(PROJECT_ROOT / "main.py"),
    ]

    print(f"Compilando {APP_NAME} v{__version__}...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        return result.returncode

    exe_path = PROJECT_ROOT / f"{APP_NAME}.exe"
    print(f"\nListo: {exe_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
