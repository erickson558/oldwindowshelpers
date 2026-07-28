"""app/menu_actions.py fija a mano el índice de la letra subrayada
(mnemónico) de cada item del menú Win98 -- si dos items del MISMO nivel
terminan compartiendo la misma letra (por un typo al agregar un personaje o
al traducir un label), Windows 98 real simplemente no sabría a cuál saltar
al apretar esa tecla. Estas pruebas verifican que eso no pase, sin necesitar
levantar una ventana Tk real."""

import json
import tkinter as tk

import pytest

from app.animation import Assistant
from app.i18n import SUPPORTED_LANGS
from app.menu_actions import (
    _CHARACTER_MNEMONICS,
    _LANGUAGE_MNEMONICS,
    _TOP_LEVEL_MNEMONICS_ES,
    _TOP_LEVEL_MNEMONICS_EN,
)
from app.resources import resource_path
from app.win98_menu import MenuItem, Win98Menu


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


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_motion_after_submenu_reaches_a_parent_row_below_it(tk_root):
    """Bug real (v0.5.2), reportado por el usuario como "se queda trabado en
    el idioma" al moverse por el menú: con el grab global activo (ver
    _show_at), Windows puede redirigir un <Motion> real hacia el Toplevel
    del submenú que lo sostiene en ese momento, aunque el mouse ya esté de
    vuelta sobre una fila del PADRE más abajo en la cadena -- confirmado en
    vivo con un clic real, no un evento sintético de Tk. Antes de este fix,
    _on_motion interpretaba ese evento con las coordenadas LOCALES del
    canvas que "recibió" el evento (el del submenú), que nunca podían
    coincidir con una fila del padre: el highlight se quedaba pegado en el
    submenú para siempre. _dispatch_motion_by_root usa la posición ABSOLUTA
    de pantalla para encontrar el nivel correcto sin importar en qué canvas
    "aterrizó" el evento."""
    below_item = MenuItem(kind="command", label="Below")
    cascade_item = MenuItem(
        kind="cascade",
        label="Cascade",
        submenu=[MenuItem(kind="command", label="Child A"), MenuItem(kind="command", label="Child B")],
    )
    menu = Win98Menu(tk_root, [cascade_item, below_item])
    try:
        menu.popup(100, 100)
        menu._set_highlight(0)
        menu._open_submenu_for(0, focus_first=True)
        assert menu.child is not None, "el submenu deberia haberse abierto"

        below_row = menu._rows[1]
        below_x_root = menu._x + menu.full_width // 2
        below_y_root = menu._y + (below_row["y0"] + below_row["y1"]) // 2

        # Simula el <Motion> llegando al canvas del HIJO (como pasaria con el
        # grab redirigiendolo), con coordenadas raiz reales sobre la fila
        # "Below" del PADRE -- exactamente el escenario roto.
        menu.child._dispatch_motion_by_root(below_x_root, below_y_root)

        assert menu.highlighted == 1, "el hover deberia haber saltado a la fila del padre, no quedarse en el submenu"
        assert menu.child is None, "el submenu deberia haberse cerrado al mover el highlight del padre"
    finally:
        menu.close()
