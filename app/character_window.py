"""Ventana flotante sin bordes que muestra al personaje animado sobre el escritorio.

Truco de transparencia: en Windows, Tk permite declarar un color "llave" con
`-transparentcolor` — cualquier píxel de ese color exacto se vuelve invisible
(clic incluido) y se ve el escritorio detrás. Ponemos ese mismo color como
fondo del Label que contiene el sprite, así solo se ve el personaje (con sus
bordes antialiased fundiéndose en el color llave, imperceptible en la práctica).
Es la técnica estándar para "mascotas de escritorio" en Tkinter.
"""

import tkinter as tk

from .animation import Assistant

TRANSPARENT_KEY = "#ff00ff"  # magenta puro: prácticamente nunca aparece en el arte de estos personajes
BUBBLE_BG = "#ffffe1"  # amarillo pálido clásico de globo de ayuda de Windows


class CharacterWindow:
    def __init__(self, root: tk.Tk, character_name: str, on_right_click, on_drag_end):
        self.root = root
        self.on_right_click = on_right_click
        self.on_drag_end = on_drag_end

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-transparentcolor", TRANSPARENT_KEY)
        self.window.configure(bg=TRANSPARENT_KEY)

        self.label = tk.Label(self.window, bg=TRANSPARENT_KEY, bd=0)
        self.label.pack()
        self.label.bind("<Button-3>", self._handle_right_click)
        self.label.bind("<ButtonPress-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._do_drag)

        self._drag_offset = (0, 0)
        self._current_animation = None
        self._current_frame = 0
        self._after_id = None
        self._one_shot_queue: list[tuple[str, callable | None]] = []

        self.assistant = Assistant(character_name)
        self._position_window(None)
        self.play_idle()

    # --- posicionamiento y arrastre -------------------------------------------------
    def _position_window(self, position: tuple[int, int] | None) -> None:
        if position is None:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = screen_w - self.assistant.frame_width - 40
            y = screen_h - self.assistant.frame_height - 80
        else:
            x, y = position
        self.window.geometry(f"+{x}+{y}")

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_offset = (event.x, event.y)

    def _do_drag(self, event: tk.Event) -> None:
        x = self.window.winfo_x() + event.x - self._drag_offset[0]
        y = self.window.winfo_y() + event.y - self._drag_offset[1]
        self.window.geometry(f"+{x}+{y}")
        self.on_drag_end((x, y))

    def _handle_right_click(self, event: tk.Event) -> None:
        self.on_right_click(event.x_root, event.y_root)

    # --- animación --------------------------------------------------------------
    def play_idle(self) -> None:
        self._play(self.assistant.pick_idle_animation(), loop=True)

    def play_once(self, animation: str, on_complete=None) -> None:
        self._play(animation, loop=False, on_complete=on_complete)

    def _play(self, animation: str, loop: bool, on_complete=None) -> None:
        if self._after_id is not None:
            self.window.after_cancel(self._after_id)
            self._after_id = None
        self._current_animation = animation
        self._current_frame = 0
        self._advance_frame(loop=loop, on_complete=on_complete)

    def _advance_frame(self, loop: bool, on_complete=None) -> None:
        animation = self._current_animation
        total = self.assistant.frame_count(animation)
        if self._current_frame >= total:
            if loop:
                self.play_idle()
            else:
                self.play_idle()
                if on_complete:
                    on_complete()
            return

        photo = self.assistant.frame_image(animation, self._current_frame)
        self.label.configure(image=photo)
        self.label.image = photo  # evita que el garbage collector se lo lleve
        duration = self.assistant.frame_duration_ms(animation, self._current_frame)
        self._current_frame += 1
        self._after_id = self.window.after(
            duration, lambda: self._advance_frame(loop=loop, on_complete=on_complete)
        )

    def set_character(self, character_name: str) -> None:
        self.assistant = Assistant(character_name)
        self.play_idle()

    # --- utilidades de ventana ----------------------------------------------------
    def set_always_on_top(self, value: bool) -> None:
        self.window.attributes("-topmost", value)

    def hide(self) -> None:
        self.window.withdraw()

    def show(self) -> None:
        self.window.deiconify()

    def is_visible(self) -> bool:
        return self.window.state() != "withdrawn"

    def show_speech_bubble(self, text: str, duration_ms: int = 4000) -> None:
        bubble = tk.Toplevel(self.window)
        bubble.overrideredirect(True)
        bubble.attributes("-topmost", True)
        label = tk.Label(
            bubble,
            text=text,
            bg=BUBBLE_BG,
            fg="#000000",
            font=("Comic Sans MS", 9),
            wraplength=220,
            justify="left",
            padx=10,
            pady=8,
            relief="solid",
            bd=1,
        )
        label.pack()

        x = self.window.winfo_x() - 200
        y = self.window.winfo_y() - 20
        bubble.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        bubble.after(duration_ms, bubble.destroy)
