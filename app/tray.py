"""Icono en la bandeja del sistema (system tray), para poder reabrir/controlar
la app incluso si el personaje flotante está oculto.

pystray corre su propio bucle de eventos en un hilo aparte, así que cada acción
se reenvía al hilo principal de Tkinter con `root.after(0, ...)` — Tkinter no es
thread-safe y todo lo que toque la UI debe ejecutarse en su propio hilo.
"""

import threading
import webbrowser

import pystray
from PIL import Image

from .i18n import SUPPORTED_LANGS
from .menu_actions import BUY_ME_A_BEER_URL
from .resources import resource_path

ICON_FILE = "clippy_icon_136771.ico"


def _run_on_ui_thread(app, func):
    def wrapper(icon=None, item=None):
        app.root.after(0, func)

    return wrapper


def build_tray_icon(app) -> pystray.Icon:
    t = app.i18n.t
    image = Image.open(resource_path(ICON_FILE))

    def _set_character(name):
        return _run_on_ui_thread(app, lambda: app.change_character(name))

    def _set_language(lang):
        return _run_on_ui_thread(app, lambda: app.set_language(lang))

    from .animation import Assistant

    characters_submenu = pystray.Menu(
        *[
            pystray.MenuItem(
                name,
                _set_character(name),
                radio=True,
                checked=lambda item, n=name: app.character_var.get() == n,
            )
            for name in Assistant.available()
        ]
    )
    language_submenu = pystray.Menu(
        *[
            pystray.MenuItem(
                lang.upper(),
                _set_language(lang),
                radio=True,
                checked=lambda item, l=lang: app.language_var.get() == l,
            )
            for lang in SUPPORTED_LANGS
        ]
    )

    menu = pystray.Menu(
        pystray.MenuItem(t("menu.change_character"), characters_submenu),
        pystray.MenuItem(t("menu.say_tip"), _run_on_ui_thread(app, app.say_tip)),
        pystray.MenuItem(t("menu.windows_help"), _run_on_ui_thread(app, app.open_windows_help)),
        pystray.MenuItem(
            t("menu.always_on_top"),
            _run_on_ui_thread(app, app.toggle_always_on_top),
            checked=lambda item: app.always_on_top_var.get(),
        ),
        pystray.MenuItem(
            t("menu.show"),
            _run_on_ui_thread(app, app.show_character),
            visible=lambda item: not app.character_window.is_visible(),
        ),
        pystray.MenuItem(
            t("menu.hide"),
            _run_on_ui_thread(app, app.hide_character),
            visible=lambda item: app.character_window.is_visible(),
        ),
        pystray.MenuItem(t("menu.language"), language_submenu),
        pystray.MenuItem(
            t("menu.start_with_windows"),
            _run_on_ui_thread(app, app.toggle_start_with_windows),
            checked=lambda item: app.start_with_windows_var.get(),
        ),
        pystray.MenuItem(t("menu.about"), _run_on_ui_thread(app, app.show_about)),
        pystray.MenuItem(t("menu.buy_beer"), lambda icon, item: webbrowser.open(BUY_ME_A_BEER_URL)),
        pystray.MenuItem(t("menu.exit"), _run_on_ui_thread(app, app.exit_app)),
    )

    icon = pystray.Icon("OldWindowsHelpers", image, t("app.name"), menu)
    return icon


def start_tray_icon(app) -> threading.Thread:
    icon = build_tray_icon(app)
    app.tray_icon = icon
    thread = threading.Thread(target=icon.run, daemon=True)
    thread.start()
    return thread
