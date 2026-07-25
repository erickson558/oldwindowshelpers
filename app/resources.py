"""Resolución de rutas a recursos (assets, locales, icono).

Cuando la app corre como script normal, los recursos están junto al código fuente.
Cuando PyInstaller la empaqueta en un .exe (--onefile), los extrae a una carpeta
temporal y expone esa ruta en sys._MEIPASS. Este módulo abstrae esa diferencia
para que el resto del código nunca tenga que pensar en si está "congelado" o no.
"""

import sys
from pathlib import Path


def base_path() -> Path:
    """Carpeta raíz desde la que se sirven los recursos (fuente o bundle de PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """Construye una ruta absoluta a un recurso dado, relativa a base_path()."""
    return base_path().joinpath(*parts)
