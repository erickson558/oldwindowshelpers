"""Persistencia de configuración del usuario y arranque automático con Windows.

La config vive en %APPDATA%\\OldWindowsHelpers\\config.json (no en la carpeta de
instalación) para que funcione igual corriendo desde código fuente o como .exe,
y para que cada usuario de la PC tenga su propia preferencia.
"""

import json
import os
import sys
import winreg
from pathlib import Path

APP_NAME = "OldWindowsHelpers"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

DEFAULTS = {
    "character": "Clippy",
    "language": None,  # None = detectar del sistema
    "always_on_top": True,
    "position": None,  # [x, y] o None = posición por defecto
    "start_with_windows": False,
}


def _config_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    directory = Path(appdata) / APP_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _config_path() -> Path:
    return _config_dir() / "config.json"


def load() -> dict:
    path = _config_path()
    if not path.exists():
        return dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(config: dict) -> None:
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _executable_command() -> str:
    """Comando a registrar para el autoarranque: el propio .exe, o `pythonw main.py` en modo desarrollo."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{interpreter}" "{main_py}"'


def set_start_with_windows(enabled: bool) -> None:
    """Crea o borra la entrada en el Run key de HKCU (no requiere admin, solo afecta al usuario actual)."""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _executable_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def is_start_with_windows_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
