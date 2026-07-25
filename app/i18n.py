"""Soporte multi-idioma (i18n) muy simple basado en diccionarios JSON.

Cada idioma vive en locales/<codigo>.json como un mapa plano clave -> texto.
Si una clave falta en el idioma activo, se cae a inglés; si tampoco está ahí,
se devuelve la propia clave (para que nunca se rompa la UI por una traducción
faltante).
"""

import ctypes
import json

from .resources import resource_path

DEFAULT_LANG = "es"
FALLBACK_LANG = "en"
SUPPORTED_LANGS = ("es", "en")

_cache: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang in _cache:
        return _cache[lang]
    path = resource_path("locales", f"{lang}.json")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    _cache[lang] = data
    return data


def detect_system_language() -> str:
    """Usa la API de Windows (evita el módulo locale, deprecado/poco fiable para esto)."""
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
        primary_lang = lang_id & 0x3FF
        LANG_ENGLISH = 0x09
        return "en" if primary_lang == LANG_ENGLISH else DEFAULT_LANG
    except Exception:
        return DEFAULT_LANG


class Translator:
    """Traductor con estado (idioma activo) usado por toda la UI."""

    def __init__(self, lang: str | None = None):
        self.lang = lang if lang in SUPPORTED_LANGS else detect_system_language()

    def set_language(self, lang: str) -> None:
        self.lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG

    def t(self, key: str, **kwargs) -> str:
        strings = _load(self.lang)
        value = strings.get(key, _load(FALLBACK_LANG).get(key, key))
        return value.format(**kwargs) if kwargs else value

    def list(self, key: str) -> list[str]:
        strings = _load(self.lang)
        value = strings.get(key, _load(FALLBACK_LANG).get(key, []))
        return value if isinstance(value, list) else [str(value)]
