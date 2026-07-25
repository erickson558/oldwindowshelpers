"""Construye el menú contextual (clic derecho) sobre el personaje.

Se arma en base a los métodos y el estado expuestos por `app` (la instancia de
OldWindowsHelpersApp en main.py) y las cadenas traducidas de `app.i18n`. Tanto
la ventana flotante como el icono de bandeja (tray.py) usan las mismas acciones,
así que viven acá una sola vez.
"""

import tkinter as tk
import webbrowser

from .animation import Assistant
from .i18n import SUPPORTED_LANGS

BUY_ME_A_BEER_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


def build_context_menu(app, parent: tk.Misc) -> tk.Menu:
    t = app.i18n.t
    menu = tk.Menu(parent, tearoff=0)

    characters_menu = tk.Menu(menu, tearoff=0)
    for name in Assistant.available():
        characters_menu.add_radiobutton(
            label=name,
            value=name,
            variable=app.character_var,
            command=lambda n=name: app.change_character(n),
        )
    menu.add_cascade(label=t("menu.change_character"), menu=characters_menu)

    menu.add_command(label=t("menu.say_tip"), command=app.say_tip)
    menu.add_command(label=t("menu.windows_help"), command=app.open_windows_help)
    menu.add_separator()

    menu.add_checkbutton(
        label=t("menu.always_on_top"),
        variable=app.always_on_top_var,
        command=app.toggle_always_on_top,
    )
    menu.add_command(label=t("menu.hide"), command=app.hide_character)

    language_menu = tk.Menu(menu, tearoff=0)
    for lang in SUPPORTED_LANGS:
        language_menu.add_radiobutton(
            label=lang.upper(),
            value=lang,
            variable=app.language_var,
            command=lambda l=lang: app.set_language(l),
        )
    menu.add_cascade(label=t("menu.language"), menu=language_menu)

    menu.add_checkbutton(
        label=t("menu.start_with_windows"),
        variable=app.start_with_windows_var,
        command=app.toggle_start_with_windows,
    )
    menu.add_separator()

    menu.add_command(label=t("menu.about"), command=app.show_about)
    menu.add_command(
        label=t("menu.buy_beer"), command=lambda: webbrowser.open(BUY_ME_A_BEER_URL)
    )
    menu.add_separator()
    menu.add_command(label=t("menu.exit"), command=app.exit_app)

    return menu
