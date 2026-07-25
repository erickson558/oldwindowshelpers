"""Compila main.py a un .exe standalone, sin consola, con el ícono local, y lo
deja en la raíz del proyecto (misma carpeta que main.py).

Uso:
    python tools/build_exe.py

Es exactamente lo que corre .github/workflows/release.yml en CI; este script
existe para poder compilar igual en tu propia máquina sin depender de GitHub.
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


def main() -> int:
    if not ICON.exists():
        print(f"No se encontró el ícono en {ICON}")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",  # es una app de escritorio: no debe abrir consola
        "--name",
        APP_NAME,
        "--icon",
        str(ICON),
        "--add-data",
        f"{PROJECT_ROOT / 'assets'}{DATA_SEP}assets",
        "--add-data",
        f"{PROJECT_ROOT / 'locales'}{DATA_SEP}locales",
        "--add-data",
        f"{ICON}{DATA_SEP}.",
        "--distpath",
        str(PROJECT_ROOT),
        "--workpath",
        str(PROJECT_ROOT / "build"),
        "--specpath",
        str(PROJECT_ROOT / "build"),
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
