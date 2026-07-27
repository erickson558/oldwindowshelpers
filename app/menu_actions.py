"""Construye el menú contextual (clic derecho) sobre el personaje.

Se arma en base a los métodos y el estado expuestos por `app` (la instancia de
OldWindowsHelpersApp en main.py) y las cadenas traducidas de `app.i18n`. Tanto
la ventana flotante como el icono de bandeja (tray.py) usan las mismas acciones,
así que viven acá una sola vez.

Nota de alcance: el icono de la bandeja (`app/tray.py`) NO usa este menú --
pystray dibuja su propio menú nativo del sistema operativo por un camino de
render totalmente distinto (fuera de Tk), así que ese archivo sigue usando sus
propios `pystray.MenuItem`; no es un descuido que no tenga el look Win98.

Desde acá se devuelve un `Win98Menu` (ver `app/win98_menu.py`) en vez de un
`tkinter.Menu`: en Windows, `tk.Menu` delega el dibujo al menú emergente
nativo de Win32, que ignora cualquier personalización de color/fuente/borde y
no se puede animar -- por eso el reemplazo por un widget propio (Toplevel +
Canvas) con la estética y las letras mnemónicas subrayadas de Windows 98.
"""

import webbrowser

import tkinter as tk

from .animation import Assistant
from .i18n import SUPPORTED_LANGS
from .win98_menu import MenuItem, Win98Menu

BUY_ME_A_BEER_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"

# --- índices de subrayado mnemónico (0-based, misma convención que el
# `underline=` nativo de Tkinter) para cada item del nivel superior --------------
# Ya vienen colisión-verificados a mano para que dos letras no compitan en el
# mismo nivel de menú: NO se recalculan acá a partir del texto, son offsets
# fijos elegidos a propósito (dependen del idioma porque la traducción cambia
# dónde cae la letra elegida).
_TOP_LEVEL_MNEMONICS_ES = {
    "menu.change_character": 0,  # "Cambiar personaje" -> 'C'
    "menu.say_tip": 0,  # "Decime un consejo" -> 'D'
    "menu.animate": 1,  # "Animar" -> 'n'
    "menu.windows_help": 1,  # "Ayuda de Windows" -> 'y'
    "menu.always_on_top": 8,  # "Siempre visible" -> 'v' (de "visible")
    "menu.hide": 0,  # "Ocultar" -> 'O'
    "menu.language": 0,  # "Idioma" -> 'I'
    "menu.start_with_windows": 12,  # "Iniciar con Windows" -> 'W' (de "Windows")
    "menu.about": 0,  # "Acerca de" -> 'A'
    "menu.buy_beer": 20,  # "☕ Cómprame una cerveza" -> 'z' (de "cerveza")
    "menu.exit": 0,  # "Salir" -> 'S'
}
_TOP_LEVEL_MNEMONICS_EN = {
    "menu.change_character": 0,  # "Change character" -> 'C'
    "menu.say_tip": 0,  # "Give me a tip" -> 'G'
    "menu.animate": 1,  # "Animate" -> 'n'
    "menu.windows_help": 8,  # "Windows Help" -> 'H' (de "Help")
    "menu.always_on_top": 4,  # "Always on top" -> 'y' (de "Always")
    "menu.hide": 1,  # "Hide" -> 'i'
    "menu.language": 0,  # "Language" -> 'L'
    "menu.start_with_windows": 0,  # "Start with Windows" -> 'S'
    "menu.about": 0,  # "About" -> 'A'
    "menu.buy_beer": 2,  # "☕ Buy me a beer" -> 'B'
    "menu.exit": 0,  # "Exit" -> 'E'
}

# Submenú de personajes: independiente del idioma (son nombres propios, ver
# Assistant.available()).
_CHARACTER_MNEMONICS = {
    "Clippy": 0,
    "Dot": 0,
    "F1": 0,
    "Genius": 0,
    "Kairu": 0,
    "Links": 0,
    "Merlin": 0,
    "MonkeyKing": 5,  # 'y' de "Monkey"
    "MotherNature": 6,  # 'N' de "Nature"
    "OfficeLogo": 0,
    "PowerPup": 0,
    "Rocky": 0,
    "SaekoSensei": 0,
    "Scribble": 4,  # 'b' de "Scribble"
    "Will": 0,
}

# Submenú de idioma: las etiquetas son literalmente "ES"/"EN" en ambos idiomas.
_LANGUAGE_MNEMONICS = {"es": 0, "en": 1}


def build_context_menu(app, parent: tk.Misc) -> Win98Menu:
    t = app.i18n.t
    mnemonics = _TOP_LEVEL_MNEMONICS_ES if app.i18n.lang == "es" else _TOP_LEVEL_MNEMONICS_EN

    character_items = [
        MenuItem(
            kind="radio",
            label=name,
            underline=_CHARACTER_MNEMONICS.get(name, -1),
            variable=app.character_var,
            value=name,
            command=lambda n=name: app.change_character(n),
        )
        for name in Assistant.available()
    ]

    language_items = [
        MenuItem(
            kind="radio",
            label=lang.upper(),
            underline=_LANGUAGE_MNEMONICS.get(lang, -1),
            variable=app.language_var,
            value=lang,
            command=lambda l=lang: app.set_language(l),
        )
        for lang in SUPPORTED_LANGS
    ]

    items = [
        MenuItem(
            kind="cascade",
            label=t("menu.change_character"),
            underline=mnemonics["menu.change_character"],
            submenu=character_items,
        ),
        MenuItem(
            kind="command",
            label=t("menu.say_tip"),
            underline=mnemonics["menu.say_tip"],
            command=app.say_tip,
        ),
        MenuItem(
            kind="command",
            label=t("menu.animate"),
            underline=mnemonics["menu.animate"],
            command=app.animate_character,
        ),
        MenuItem(
            kind="command",
            label=t("menu.windows_help"),
            underline=mnemonics["menu.windows_help"],
            command=app.open_windows_help,
        ),
        MenuItem(kind="separator"),
        MenuItem(
            kind="check",
            label=t("menu.always_on_top"),
            underline=mnemonics["menu.always_on_top"],
            variable=app.always_on_top_var,
            command=app.toggle_always_on_top,
        ),
        MenuItem(
            kind="command",
            label=t("menu.hide"),
            underline=mnemonics["menu.hide"],
            command=app.hide_character,
        ),
        MenuItem(
            kind="cascade",
            label=t("menu.language"),
            underline=mnemonics["menu.language"],
            submenu=language_items,
        ),
        MenuItem(
            kind="check",
            label=t("menu.start_with_windows"),
            underline=mnemonics["menu.start_with_windows"],
            variable=app.start_with_windows_var,
            command=app.toggle_start_with_windows,
        ),
        MenuItem(kind="separator"),
        MenuItem(
            kind="command",
            label=t("menu.about"),
            underline=mnemonics["menu.about"],
            command=app.show_about,
        ),
        MenuItem(
            kind="command",
            label=t("menu.buy_beer"),
            underline=mnemonics["menu.buy_beer"],
            command=lambda: webbrowser.open(BUY_ME_A_BEER_URL),
        ),
        MenuItem(kind="separator"),
        MenuItem(
            kind="command",
            label=t("menu.exit"),
            underline=mnemonics["menu.exit"],
            command=app.exit_app,
        ),
    ]

    return Win98Menu(parent, items)
