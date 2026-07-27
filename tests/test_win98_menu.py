"""app/menu_actions.py fija a mano el índice de la letra subrayada
(mnemónico) de cada item del menú Win98 -- si dos items del MISMO nivel
terminan compartiendo la misma letra (por un typo al agregar un personaje o
al traducir un label), Windows 98 real simplemente no sabría a cuál saltar
al apretar esa tecla. Estas pruebas verifican que eso no pase, sin necesitar
levantar una ventana Tk real."""

import json

from app.animation import Assistant
from app.i18n import SUPPORTED_LANGS
from app.menu_actions import (
    _CHARACTER_MNEMONICS,
    _LANGUAGE_MNEMONICS,
    _TOP_LEVEL_MNEMONICS_ES,
    _TOP_LEVEL_MNEMONICS_EN,
)
from app.resources import resource_path


def _assert_no_collisions(labels_by_key: dict[str, str], mnemonics_by_key: dict[str, int], level_name: str):
    seen: dict[str, str] = {}
    for key, label in labels_by_key.items():
        index = mnemonics_by_key.get(key, -1)
        assert 0 <= index < len(label), (
            f"{level_name}/{key}: indice de mnemonico {index} fuera de rango para '{label}'"
        )
        letter = label[index].lower()
        assert letter not in seen, (
            f"{level_name}: '{key}' y '{seen.get(letter)}' comparten el mnemonico '{letter}' "
            f"-- Windows 98 no podria saber a cual saltar al apretar esa tecla"
        )
        seen[letter] = key


def test_top_level_mnemonics_have_no_collisions_es():
    labels = json.loads(resource_path("locales", "es.json").read_text(encoding="utf-8"))
    _assert_no_collisions(
        {key: labels[key] for key in _TOP_LEVEL_MNEMONICS_ES}, _TOP_LEVEL_MNEMONICS_ES, "top-level ES"
    )


def test_top_level_mnemonics_have_no_collisions_en():
    labels = json.loads(resource_path("locales", "en.json").read_text(encoding="utf-8"))
    _assert_no_collisions(
        {key: labels[key] for key in _TOP_LEVEL_MNEMONICS_EN}, _TOP_LEVEL_MNEMONICS_EN, "top-level EN"
    )


def test_character_submenu_mnemonics_have_no_collisions():
    names = Assistant.available() or list(_CHARACTER_MNEMONICS)
    _assert_no_collisions({name: name for name in names}, _CHARACTER_MNEMONICS, "characters")


def test_language_submenu_mnemonics_have_no_collisions():
    labels = {lang: lang.upper() for lang in SUPPORTED_LANGS}
    _assert_no_collisions(labels, _LANGUAGE_MNEMONICS, "language")
