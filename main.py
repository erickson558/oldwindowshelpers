"""Punto de entrada de Ayudantes de Office / Office Helpers.

Arma la ventana flotante del personaje, la bandeja del sistema y conecta las
acciones del menú de clic derecho. Pensado para correr sin consola (ver
tools/build_exe.py) y quedar dando vueltas en segundo plano como un widget de
escritorio nostálgico.
"""

import random
import sys
import tkinter as tk
from tkinter import messagebox

from app import settings
from app.animation import Assistant
from app.character_window import CharacterWindow
from app.i18n import Translator
from app.menu_actions import build_context_menu
from app.signature_actions import get_signature_animation
from app.tray import start_tray_icon
from app.windows_help import trigger_windows_help
from version import __version__

AUTO_TIP_INTERVAL_MS = 15 * 60 * 1000  # cada 15 minutos, el personaje tira un consejo solo


class OldWindowsHelpersApp:
    def __init__(self):
        self.config = settings.load()

        self.root = tk.Tk()
        self.root.withdraw()  # no queremos la ventana principal de Tk, solo el personaje flotante

        self.i18n = Translator(self.config.get("language"))

        available = Assistant.available()
        character = self.config.get("character") or "Clippy"
        if character not in available and available:
            character = available[0]

        self.character_var = tk.StringVar(value=character)
        self.language_var = tk.StringVar(value=self.i18n.lang)
        self.always_on_top_var = tk.BooleanVar(value=self.config.get("always_on_top", True))
        self.start_with_windows_var = tk.BooleanVar(
            value=settings.is_start_with_windows_enabled()
        )

        self.character_window = CharacterWindow(
            self.root,
            character,
            on_right_click=self.show_context_menu,
            on_drag_end=self.on_drag_end,
        )
        self.character_window.set_always_on_top(self.always_on_top_var.get())

        self.tray_icon = None
        start_tray_icon(self)

        self.root.after(AUTO_TIP_INTERVAL_MS, self._auto_tip_loop)

    # --- acciones invocadas desde el menú (ventana o bandeja) ----------------------
    def show_context_menu(self, x: int, y: int) -> None:
        menu = build_context_menu(self, self.character_window.window)
        menu.tk_popup(x, y)

    def change_character(self, name: str) -> None:
        self.character_var.set(name)
        self.character_window.set_character(name)
        self.config["character"] = name
        settings.save(self.config)

    def say_tip(self) -> None:
        tip = random.choice(self.i18n.list("tips"))
        one_shot = self.character_window.assistant.one_shot_animations()
        self.character_window.play_once(random.choice(one_shot))
        self.character_window.show_speech_bubble(tip)

    def animate_character(self) -> None:
        """"Animar": a diferencia de "Decime un consejo" (animación al azar),
        reproduce el gesto de firma del personaje activo (ver
        app/signature_actions.py) junto con su frase característica."""
        assistant = self.character_window.assistant
        animation = get_signature_animation(assistant)
        quip_key = f"animate.{assistant.name}"
        quip = self.i18n.t(quip_key)
        if quip == quip_key:  # no hay traducción para este personaje: usar un consejo genérico
            quip = random.choice(self.i18n.list("tips"))
        self.character_window.play_once(animation)
        self.character_window.show_speech_bubble(quip)

    def open_windows_help(self) -> None:
        trigger_windows_help()

    def toggle_always_on_top(self) -> None:
        value = self.always_on_top_var.get()
        self.character_window.set_always_on_top(value)
        self.config["always_on_top"] = value
        settings.save(self.config)

    def hide_character(self) -> None:
        self.character_window.hide()

    def show_character(self) -> None:
        self.character_window.show()

    def on_drag_end(self, position: tuple[int, int]) -> None:
        self.config["position"] = list(position)
        settings.save(self.config)

    def set_language(self, lang: str) -> None:
        self.i18n.set_language(lang)
        self.language_var.set(lang)
        self.config["language"] = lang
        settings.save(self.config)

    def toggle_start_with_windows(self) -> None:
        value = self.start_with_windows_var.get()
        settings.set_start_with_windows(value)
        self.config["start_with_windows"] = value
        settings.save(self.config)

    def show_about(self) -> None:
        messagebox.showinfo(
            self.i18n.t("about.title"),
            self.i18n.t("about.body", version=__version__),
        )

    def exit_app(self) -> None:
        if self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.quit()

    def _auto_tip_loop(self) -> None:
        if self.character_window.is_visible():
            self.say_tip()
        self.root.after(AUTO_TIP_INTERVAL_MS, self._auto_tip_loop)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    app = OldWindowsHelpersApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
