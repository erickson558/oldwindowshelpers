"""Menú contextual estilo Windows 98, dibujado a mano con Canvas.

Por qué existe este archivo (no alcanza con `tkinter.Menu`): en Windows,
`tk.Menu` delega el dibujo al menú emergente nativo de Win32. Ese menú nativo
ignora `bg`/`activebackground`/`font`/`border` (los pinta el propio Windows con
el tema del sistema) y no se puede animar cuadro a cuadro desde Tcl/Tk. Como
acá queremos la estética Win98 real (gris #C0C0C0, selección azul marino,
letras subrayadas SIEMPRE visibles, animación de "desenrollado") no queda otra
que reconstruir el menú desde cero: un `Toplevel` sin bordes (overrideredirect)
con un `Canvas` adentro que nosotros mismos dibujamos, posicionamos y animamos.

Piezas principales:
  - `MenuItem`: describe una fila (comando simple, checkbutton, radiobutton,
    separador o cascada/submenú) más el índice de carácter a subrayar como
    mnemónico. Los índices los decide quien arma el menú (ver
    `menu_actions.py`) — acá solo se dibujan y se usan para el atajo de
    teclado, no se recalculan.
  - `Win98Menu`: un `Toplevel` + `Canvas` que representa UN nivel del menú
    (el nivel superior, o un submenú abierto). Cada cascada abierta es una
    instancia hija encadenada vía `parent`/`child`, para poder cerrarlas todas
    juntas (clic afuera, Escape en el nivel superior) o de a una
    (flecha Izquierda, Escape dentro de un submenú).

Nota de alcance: esto NO toca `app/tray.py`. El ícono de la bandeja usa
`pystray`, que dibuja su propio menú nativo del sistema operativo por un
camino de render totalmente distinto (fuera de Tk) y no admite este mismo
estilo; que ese archivo no tenga esta skin no es un descuido.
"""

from __future__ import annotations

import ctypes
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import dataclass

# --- paleta clásica "Windows Standard" (Win98/Win2000 look) --------------------
FACE_BG = "#C0C0C0"
TEXT_FG = "#000000"
SELECTED_BG = "#000080"  # navy
SELECTED_FG = "#FFFFFF"
BORDER_COLOR = "#000000"
GROOVE_DARK = "#808080"
GROOVE_LIGHT = "#FFFFFF"

# --- geometría de las filas -----------------------------------------------------
BORDER = 1  # 1px de marco negro alrededor de todo el popup/submenú
PAD_V = 2  # aire arriba del primer item y debajo del último
ITEM_HEIGHT = 20
SEP_HEIGHT = 6  # alto reservado para un separador (línea "groove" de 2px + aire)
GUTTER_WIDTH = 22  # columna izquierda para el tilde/bullet de check y radio
H_PADDING = 6  # separación entre el gutter y el texto, y entre el texto y el borde
RIGHT_PADDING = 18  # espacio a la derecha reservado para la flechita de cascada
MIN_WIDTH = 120

# --- animación "Scroll" (desenrollado hacia abajo) -----------------------------
ANIMATION_DURATION_MS = 140
ANIMATION_STEPS = 7

# Cada cuánto (ms) se sondea la posición real del mouse mientras el menú está
# abierto -- ver _poll_hover más abajo para el motivo: no alcanza con el
# evento <Motion> de Tk.
HOVER_POLL_INTERVAL_MS = 50


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _get_cursor_pos() -> tuple[int, int]:
    point = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def _find_font(candidates: tuple[str, ...], size: int) -> tkfont.Font:
    """Busca la primera fuente disponible de una lista de preferencias.

    "MS Sans Serif" es la fuente period-correct de los menús de Windows 98,
    pero en una máquina moderna casi seguro no está instalada (se dejó de
    tipear en XP), así que probamos alternativas razonables y, en el peor
    caso, usamos la fuente por defecto de Tk en vez de fallar.
    """
    available = set(tkfont.families())
    for name in candidates:
        if name in available:
            return tkfont.Font(family=name, size=size)
    return tkfont.Font(size=size)


@dataclass
class MenuItem:
    """Una fila del menú. `underline` es el índice (0-based, misma convención
    que el `underline=` nativo de Tkinter) del carácter de `label` que debe
    dibujarse subrayado como mnemónico; -1 si no tiene."""

    kind: str  # "command" | "check" | "radio" | "separator" | "cascade"
    label: str = ""
    underline: int = -1
    command: Callable[[], None] | None = None
    variable: tk.Variable | None = None  # BooleanVar (check) o StringVar (radio)
    value: object = None  # valor propio de este item cuando kind == "radio"
    submenu: list[MenuItem] | None = None  # items hijos cuando kind == "cascade"

    def is_selectable(self) -> bool:
        return self.kind != "separator"

    def is_checked(self) -> bool:
        if self.kind == "check" and self.variable is not None:
            return bool(self.variable.get())
        if self.kind == "radio" and self.variable is not None:
            return self.variable.get() == self.value
        return False


class Win98Menu:
    """Un nivel de menú (nivel superior o un submenú abierto). Ver el
    docstring del módulo para la idea general."""

    def __init__(
        self,
        master: tk.Misc,
        items: list[MenuItem],
        *,
        font: tkfont.Font | None = None,
        parent: Win98Menu | None = None,
        on_fully_closed: Callable[[], None] | None = None,
    ):
        self.master = master
        self.items = items
        self.parent = parent
        self.child: Win98Menu | None = None
        self._child_index: int | None = None
        self.on_fully_closed = on_fully_closed
        self.highlighted = -1
        self._after_ids: list[str] = []
        self._closed = False
        self._global_click_bind: str | None = None
        self._grabbed = False
        self._x = 0
        self._y = 0

        self.font = font or _find_font(("MS Sans Serif", "Segoe UI"), 9)
        self._selectable_indices = [i for i, it in enumerate(items) if it.is_selectable()]

        self._layout()

        # Toplevel sin bordes de ventana: nosotros dibujamos hasta el marco.
        # Empieza oculto (withdraw) para no ver un parpadeo en (0,0) antes de
        # que `popup()`/`_open_submenu_for()` lo reposicionen.
        self.window = tk.Toplevel(master)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        # El fondo del Toplevel queda como marco: el Canvas se ubica 1px
        # adentro por cada lado (ver `place` abajo), así el borde de 1px negro
        # rodea el menú entero sin tener que dibujar 4 líneas a mano.
        self.window.configure(bg=BORDER_COLOR)

        self.canvas = tk.Canvas(
            self.window,
            bg=FACE_BG,
            highlightthickness=0,
            bd=0,
            width=self.full_width - 2 * BORDER,
            height=self.full_height - 2 * BORDER,
        )
        # Truco clave de la animación: Canvas recorta su propio contenido al
        # tamaño que tenga en cada momento (no hace falta scroll ni volver a
        # dibujar). Arrancamos con height=0 y lo vamos agrandando en
        # `_animate_open`, lo que revela el menú de arriba hacia abajo.
        self.canvas.place(x=BORDER, y=BORDER, width=self.full_width - 2 * BORDER, height=0)

        self._draw_items()
        self._redraw_highlight()

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_click)
        self.window.bind("<KeyPress>", self._on_key)
        self.window.bind("<Escape>", lambda e: self._on_escape())

        if self.parent is None:
            # Solo el nivel superior escucha clics globales: si el clic no
            # cayó en ninguna ventana de la cadena (este menú o alguno de sus
            # submenús abiertos), cerramos todo. Un submenú no necesita este
            # bind porque ya está cubierto por el de su ancestro raíz.
            self._global_click_bind = self.master.bind_all(
                "<ButtonPress-1>", self._on_global_click, add="+"
            )

    # --- layout / dibujo ---------------------------------------------------------
    def _layout(self) -> None:
        """Calcula alto/ancho totales y la caja (y0, y1) de cada fila. Se hace
        una sola vez al construir el menú (los items no cambian mientras está
        abierto)."""
        y = BORDER + PAD_V
        self._rows: list[dict] = []
        max_text_width = 0
        for idx, item in enumerate(self.items):
            if item.kind == "separator":
                y0, y1 = y, y + SEP_HEIGHT
            else:
                y0, y1 = y, y + ITEM_HEIGHT
                max_text_width = max(max_text_width, self.font.measure(item.label))
            self._rows.append({"item": item, "index": idx, "y0": y0, "y1": y1})
            y = y1
        self.full_height = y + PAD_V + BORDER
        content_width = GUTTER_WIDTH + H_PADDING + max_text_width + RIGHT_PADDING
        self.full_width = max(MIN_WIDTH, content_width) + 2 * BORDER

    def _draw_items(self) -> None:
        # `row["y0"]/row["y1"]` están en coordenadas de VENTANA (incluyen el
        # marco de 1px, ver `_layout`), pero acá dibujamos sobre `self.canvas`,
        # que ya está desplazado BORDER píxeles adentro del Toplevel -- hay
        # que restar ese offset para que coincida con lo que en verdad se ve.
        for row in self._rows:
            item: MenuItem = row["item"]
            y0, y1 = row["y0"] - BORDER, row["y1"] - BORDER
            if item.kind == "separator":
                # Línea "groove" clásica: un píxel oscuro seguido de uno
                # claro, que da el efecto hundido típico de Win98/95.
                mid = (y0 + y1) // 2
                inner_w = self.full_width - 2 * BORDER
                self.canvas.create_line(2, mid, inner_w - 2, mid, fill=GROOVE_DARK)
                self.canvas.create_line(2, mid + 1, inner_w - 2, mid + 1, fill=GROOVE_LIGHT)
                row["bg_id"] = None
                row["text_id"] = None
                row["underline_id"] = None
                row["mark_id"] = None
                row["arrow_id"] = None
                continue

            row["bg_id"] = self.canvas.create_rectangle(
                0, y0, self.full_width - 2 * BORDER, y1, fill=FACE_BG, outline=""
            )

            # Gutter izquierdo: tilde de check o bullet de radio, solo cuando
            # el item está activo (así se ve en Win98 -- si no está tildado,
            # el gutter queda vacío, no se dibuja una casilla vacía).
            row["mark_id"] = None
            if item.is_checked():
                cy = (y0 + y1) // 2
                if item.kind == "check":
                    self.canvas.create_rectangle(4, cy - 6, 16, cy + 6, outline=GROOVE_DARK)
                    row["mark_id"] = self.canvas.create_text(
                        10, cy, text="✓", font=self.font, fill=TEXT_FG
                    )
                else:  # radio
                    row["mark_id"] = self.canvas.create_oval(
                        7, cy - 3, 13, cy + 3, fill=TEXT_FG, outline=TEXT_FG
                    )

            text_x = GUTTER_WIDTH + H_PADDING
            text_y = (y0 + y1) // 2
            row["text_id"] = self.canvas.create_text(
                text_x, text_y, text=item.label, font=self.font, fill=TEXT_FG, anchor="w"
            )

            # Mnemónico: se mide con font.measure() el ancho del prefijo antes
            # de la letra y el ancho de la letra misma, y se traza una raya
            # corta debajo de esa letra -- a diferencia de Windows moderno (que
            # lo oculta hasta apretar Alt), Win98 lo muestra siempre, así que
            # lo dibujamos nosotros de una y no dependemos de ningún estado
            # oculto de Tk.
            row["underline_id"] = None
            if 0 <= item.underline < len(item.label):
                prefix_w = self.font.measure(item.label[: item.underline])
                char_w = self.font.measure(item.label[item.underline])
                ux0 = text_x + prefix_w
                uy = text_y + (self.font.metrics("linespace") // 2) - 1
                row["underline_id"] = self.canvas.create_line(
                    ux0, uy, ux0 + max(char_w, 1), uy, fill=TEXT_FG
                )

            row["arrow_id"] = None
            if item.kind == "cascade":
                ax = self.full_width - 2 * BORDER - 10
                ay = (y0 + y1) // 2
                row["arrow_id"] = self.canvas.create_polygon(
                    ax, ay - 4, ax, ay + 4, ax + 5, ay, fill=TEXT_FG
                )

    def _redraw_highlight(self) -> None:
        """Repinta fondo/texto/marcas de cada fila según cuál está resaltada.
        Barato de sobra para ~15 filas, así que lo hacemos completo cada vez
        que cambia la selección en vez de llevar un diff manual."""
        for row in self._rows:
            item: MenuItem = row["item"]
            if item.kind == "separator":
                continue
            selected = row["index"] == self.highlighted
            bg = SELECTED_BG if selected else FACE_BG
            fg = SELECTED_FG if selected else TEXT_FG
            self.canvas.itemconfigure(row["bg_id"], fill=bg)
            self.canvas.itemconfigure(row["text_id"], fill=fg)
            if row["underline_id"] is not None:
                self.canvas.itemconfigure(row["underline_id"], fill=fg)
            if row["mark_id"] is not None:
                self.canvas.itemconfigure(row["mark_id"], fill=fg)
            if row["arrow_id"] is not None:
                self.canvas.itemconfigure(row["arrow_id"], fill=fg)

    # --- apertura / animación -----------------------------------------------------
    def popup(self, x: int, y: int) -> None:
        """Punto de entrada público para el nivel superior: `main.py` llama
        acá con la posición del clic derecho en coordenadas de pantalla.
        Ajustamos si no entra en el monitor (misma esquina que usaría un menú
        nativo) y arrancamos la animación de desenrollado."""
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        if x + self.full_width > screen_w:
            x = max(0, screen_w - self.full_width)
        if y + self.full_height > screen_h:
            y = max(0, screen_h - self.full_height)
        self._show_at(x, y)

    def _show_at(self, x: int, y: int) -> None:
        self._x, self._y = x, y
        self.window.geometry(f"{self.full_width}x{2}+{x}+{y}")
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        if not self._grabbed:
            # Se probó primero con <FocusOut> y con comparar
            # GetForegroundWindow() contra nuestros propios hwnd -- verificado
            # EN VIVO que ninguno de los dos detecta de forma confiable que el
            # foco real de Windows se fue de la app: para una ventana
            # overrideredirect, Tk sigue reportando foco interno propio
            # (focus_get()) aunque Windows ya le haya dado el foco real a otra
            # ventana. grab_set_global es la técnica que documenta el propio
            # Tcl/Tk para este problema (a diferencia de grab_set, extiende el
            # grab a TODO el display, no solo a esta app) y es la que usamos
            # acá. OJO -- limitación conocida, documentada en vez de asumida:
            # en este entorno de desarrollo no fue posible confirmar con
            # automatización (SendInput/SetForegroundWindow) que el grab
            # además cierra el menú cuando el foco se lo lleva una ventana de
            # OTRO proceso -- Windows bloquea esas llamadas cuando vienen de un
            # proceso en script/segundo plano (ver specs/SPEC.md), así que ese
            # caso puntual solo se puede confirmar con una interacción real de
            # mouse/teclado de un usuario.
            #
            # IMPORTANTE (bug real de v0.5.0, corregido en v0.5.1): el grab
            # de Tcl/Tk NO se extiende a otros Toplevels de la misma app, solo
            # al Toplevel que lo pidió (y sus descendientes) -- un submenú es
            # un Toplevel SEPARADO del nivel superior. Si el nivel superior se
            # quedaba con el grab para siempre, los clics dentro de un
            # submenú abierto (ej. elegir un personaje de "Cambiar
            # personaje") nunca le llegaban a ESE Toplevel: quedaban
            # "atrapados" por el grab del padre, y el clic no hacía nada (el
            # bug reportado: "no me deja elegir otro ayudante"). La regla
            # correcta es que el grab lo sostiene SIEMPRE el nivel más
            # profundo actualmente abierto, nunca dos a la vez: cada nivel lo
            # toma al mostrarse (acá) y lo suelta al abrir un submenú propio
            # (ver _open_submenu_for) o al cerrarse, devolviéndoselo a su
            # padre si el padre sigue abierto (ver close()).
            self.window.grab_set_global()
            self._grabbed = True
        if self.parent is None:
            # Un solo sondeo por cadena (lo arranca el nivel superior; ver
            # _poll_hover) -- no hace falta uno por submenú, porque
            # _dispatch_motion_by_root ya revisa todos los niveles abiertos
            # en cada tick.
            self._poll_hover()
        self._animate_open(0)

    def _animate_open(self, step: int) -> None:
        if self._closed:
            return
        fraction = min(1.0, (step + 1) / ANIMATION_STEPS)
        content_h = max(1, int((self.full_height - 2 * BORDER) * fraction))
        frame_h = content_h + 2 * BORDER
        self.window.geometry(f"{self.full_width}x{frame_h}+{self._x}+{self._y}")
        self.canvas.place(x=BORDER, y=BORDER, width=self.full_width - 2 * BORDER, height=content_h)
        if step + 1 < ANIMATION_STEPS:
            after_id = self.window.after(
                max(1, ANIMATION_DURATION_MS // ANIMATION_STEPS),
                lambda: self._animate_open(step + 1),
            )
            self._after_ids.append(after_id)

    # --- cierre ---------------------------------------------------------------------
    def _cancel_pending_after(self) -> None:
        for after_id in self._after_ids:
            try:
                self.window.after_cancel(after_id)
            except tk.TclError:
                pass
        self._after_ids = []

    def close(self) -> None:
        """Cierra este nivel y, en cascada, todo lo que tenga abierto debajo
        (submenús hijos). Usado tanto para un cierre total (clic afuera,
        activar un comando, Escape en el nivel superior) como, recursivamente,
        para cerrar la cola de la cadena cuando se cierra un ancestro."""
        if self._closed:
            return
        self._closed = True
        if self.child is not None:
            self.child.close()
            self.child = None
        self._cancel_pending_after()
        if self._grabbed:
            try:
                self.window.grab_release()
            except tk.TclError:
                pass
            self._grabbed = False
            if self.parent is not None and not self.parent._closed:
                # Se cierra SOLO este submenú (ej. flecha Izquierda/Escape) y
                # el padre sigue vivo -- el grab global lo sostiene siempre
                # el nivel más profundo actualmente abierto, así que se lo
                # devolvemos al padre en vez de dejar la app entera sin grab
                # (lo que reabriría el bug de clics afuera de la app sin
                # cerrar nada, ver _show_at). Si en cambio toda la cadena se
                # está cerrando junta (el padre ya está marcado _closed antes
                # de llegar acá, ver más arriba), no hay a quién devolvérselo.
                try:
                    self.parent.window.grab_set_global()
                    self.parent._grabbed = True
                except tk.TclError:
                    pass
        if self.parent is None and self._global_click_bind is not None:
            # `unbind_all` limpia TODOS los binds de "<ButtonPress-1>" sobre
            # el tag "all", no solo el nuestro -- pero en esta app solo un
            # Win98Menu de nivel superior está vivo (y por lo tanto
            # registrado) a la vez, así que acá siempre es "el nuestro".
            try:
                self.master.unbind_all("<ButtonPress-1>")
            except tk.TclError:
                pass
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        if self.parent is None and self.on_fully_closed is not None:
            self.on_fully_closed()

    def _close_root(self) -> None:
        node = self
        while node.parent is not None:
            node = node.parent
        node.close()

    def _close_child(self) -> None:
        if self.child is not None:
            self.child.close()
            self.child = None

    # --- navegación por teclado -------------------------------------------------
    def _on_key(self, event: tk.Event) -> None:
        keysym = event.keysym
        if keysym == "Up":
            self._move_highlight(-1)
        elif keysym == "Down":
            self._move_highlight(1)
        elif keysym == "Right":
            self._on_right()
        elif keysym == "Left":
            self._on_left()
        elif keysym in ("Return", "KP_Enter", "space"):
            if self.highlighted >= 0:
                self._activate(self.highlighted)
        elif event.char:
            self._try_mnemonic(event.char)

    def _move_highlight(self, step: int) -> None:
        selectable = self._selectable_indices
        if not selectable:
            return
        if self.highlighted in selectable:
            pos = selectable.index(self.highlighted)
            pos = (pos + step) % len(selectable)
        else:
            pos = 0 if step > 0 else len(selectable) - 1
        self._set_highlight(selectable[pos])

    def _on_right(self) -> None:
        if self.highlighted < 0:
            return
        item = self.items[self.highlighted]
        if item.kind == "cascade":
            self._open_submenu_for(self.highlighted, focus_first=True)

    def _on_left(self) -> None:
        # "no hace nada en el nivel superior": solo un submenú (self.parent
        # no es None) sabe volver a su padre.
        if self.parent is not None:
            parent = self.parent
            self.close()
            parent.child = None
            parent.window.focus_force()

    def _on_escape(self) -> None:
        if self.parent is not None:
            parent = self.parent
            self.close()
            parent.child = None
            parent.window.focus_force()
        else:
            self.close()

    def _try_mnemonic(self, ch: str) -> None:
        ch = ch.lower()
        for idx in self._selectable_indices:
            item = self.items[idx]
            if 0 <= item.underline < len(item.label) and item.label[item.underline].lower() == ch:
                self._set_highlight(idx)
                self._activate(idx)
                return

    # --- mouse --------------------------------------------------------------------
    def _index_at_y(self, y: int) -> int | None:
        # `event.y` de un bind sobre `self.canvas` ya viene en coordenadas de
        # canvas (sin el offset del marco), así que convertimos igual que en
        # `_draw_items` antes de comparar.
        for row in self._rows:
            if row["item"].is_selectable() and row["y0"] - BORDER <= y < row["y1"] - BORDER:
                return row["index"]
        return None

    def _on_motion(self, event: tk.Event) -> None:
        # Complementa a _poll_hover (ver _show_at/_poll_hover): un <Motion>
        # real de Tk, cuando SÍ llega, es más inmediato que esperar el
        # próximo tick del sondeo (hasta HOVER_POLL_INTERVAL_MS de más),
        # así que lo aprovechamos igual -- pero no es la fuente de verdad
        # (ver por qué en el docstring de _poll_hover). No usamos
        # event.x/event.y (coordenadas LOCALES al widget que nominalmente
        # disparó el evento): con el grab activo, Windows puede redirigir el
        # <Motion> hacia el Toplevel del submenú aunque el mouse ya esté de
        # vuelta sobre una fila del padre, y ese evento igual "pertenece" al
        # canvas del submenú a nivel Tk. event.x_root/event.y_root siempre
        # son la posición absoluta real, pase lo que pase con el grab.
        self._dispatch_motion_by_root(event.x_root, event.y_root)

    def _poll_hover(self) -> None:
        """Red de seguridad ante <Motion> real: confirmado en vivo (bug
        reportado dos veces, v0.5.2 y esta corrección) que un <Motion> de Tk
        simplemente NO llega en absoluto una vez que el mouse deja la
        ventana que sostiene el grab global -- no es que llegue con las
        coordenadas de OTRO canvas (lo que _dispatch_motion_by_root ya
        resolvía), es que Windows deja de generarlo del todo para esta app
        mientras el grab lo tiene un Toplevel distinto de donde está el
        mouse. Por eso no alcanza con corregir cómo se interpreta el evento:
        hay que dejar de depender de que el evento llegue. Esto sondea la
        posición real del cursor (`GetCursorPos`, fuera del sistema de
        eventos de Tk) cada `HOVER_POLL_INTERVAL_MS` mientras el menú esté
        abierto, y aplica el mismo despacho por posición absoluta. Solo lo
        arranca el nivel superior (ver _show_at); se cancela solo al cerrar
        (los `after()` quedan trackeados en `_after_ids` como cualquier
        otro)."""
        if self._closed:
            return
        x_root, y_root = _get_cursor_pos()
        self._dispatch_motion_by_root(x_root, y_root)
        after_id = self.window.after(HOVER_POLL_INTERVAL_MS, self._poll_hover)
        self._after_ids.append(after_id)

    def _dispatch_motion_by_root(self, x_root: int, y_root: int) -> None:
        """Encuentra, por posición ABSOLUTA de pantalla, a cuál nivel de la
        cadena (el nivel superior o alguno de sus submenús abiertos)
        corresponde el mouse en este momento, y le aplica el hover ahí --
        en vez de asumir que el nivel "dueño" es el mismo widget que Tk usó
        para entregar el evento (ver el comentario en _on_motion)."""
        root = self
        while root.parent is not None:
            root = root.parent
        node: Win98Menu | None = root
        while node is not None:
            if (
                node._x <= x_root < node._x + node.full_width
                and node._y <= y_root < node._y + node.full_height
            ):
                # `_index_at_y` espera coordenadas relativas al Canvas (que
                # arranca BORDER píxeles adentro del Toplevel) -- convertimos
                # la posición absoluta de pantalla a ese mismo sistema.
                canvas_relative_y = (y_root - node._y) - BORDER
                idx = node._index_at_y(canvas_relative_y)
                if idx is not None and idx != node.highlighted:
                    node._set_highlight(idx)
                    item = node.items[idx]
                    if item.kind == "cascade":
                        node._open_submenu_for(idx, focus_first=True)
                return
            node = node.child

    def _on_click(self, event: tk.Event) -> None:
        idx = self._index_at_y(event.y)
        if idx is None:
            return
        self._set_highlight(idx)
        self._activate(idx)

    def _on_global_click(self, event: tk.Event) -> None:
        """Solo lo registra el nivel superior (ver __init__). Si el clic cayó
        fuera de toda la cadena de menús abiertos, cerramos todo; si cayó
        adentro, lo dejamos seguir su curso normal (lo procesa el bind propio
        de esa fila)."""
        w = event.widget
        node: Win98Menu | None = self
        while node is not None:
            if w is node.window or w is node.canvas:
                return
            node = node.child
        self.close()

    # --- selección / activación --------------------------------------------------
    def _set_highlight(self, index: int) -> None:
        if index == self.highlighted:
            return
        self.highlighted = index
        self._close_child()
        self._redraw_highlight()
        # Seguimos el foco de teclado con el mouse: si el usuario está
        # interactuando con este nivel, las teclas (flechas, mnemónicos)
        # tienen que llegar acá y no a un submenú que quedó abierto antes.
        self.window.focus_force()

    def _set_highlight_first(self) -> None:
        if self._selectable_indices:
            self._set_highlight(self._selectable_indices[0])

    def _activate(self, index: int) -> None:
        item = self.items[index]
        if item.kind == "cascade":
            self._open_submenu_for(index, focus_first=True)
            return
        # Igual que `tk.Menu.add_checkbutton`/`add_radiobutton`: activar la
        # fila primero actualiza la variable asociada y recién después llama
        # al command -- los callbacks de app (ver menu_actions.py) leen esa
        # variable ya actualizada (ej. toggle_always_on_top lee always_on_top_var
        # asumiendo que el toggle ya ocurrió).
        if item.kind == "check" and item.variable is not None:
            item.variable.set(not item.variable.get())
        elif item.kind == "radio" and item.variable is not None:
            item.variable.set(item.value)
        if item.command is not None:
            item.command()
        self._close_root()

    def _open_submenu_for(self, index: int, focus_first: bool) -> None:
        item = self.items[index]
        if item.kind != "cascade" or not item.submenu:
            return
        if self.child is not None and self._child_index == index:
            if focus_first:
                self.child.window.focus_force()
                if self.child.highlighted < 0:
                    self.child._set_highlight_first()
            return
        if self.child is not None:
            self.child.close()
            self.child = None

        submenu = Win98Menu(self.master, item.submenu, font=self.font, parent=self)
        self.child = submenu
        self._child_index = index

        row = self._rows[index]
        px, py = self._x, self._y
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        right_x = px + self.full_width
        if right_x + submenu.full_width > screen_w:
            x = max(0, px - submenu.full_width)
        else:
            x = right_x
        # `row["y0"]` ya está en coordenadas de ventana (relativas al propio
        # Toplevel de este menú), así que sumarlo directo a `py` (posición en
        # pantalla de ese Toplevel) alinea el submenú con esa fila.
        y = py + row["y0"]
        if y + submenu.full_height > screen_h:
            y = max(0, screen_h - submenu.full_height)

        # Le soltamos el grab a ESTE nivel antes de mostrar el submenú: el
        # grab global de Tcl/Tk no se extiende a otros Toplevels de la misma
        # app, así que si nos lo quedáramos, los clics dentro del submenú
        # (un Toplevel distinto) nunca le llegarían -- ver la nota larga en
        # _show_at. `_show_at` del submenú lo va a tomar él mismo.
        if self._grabbed:
            try:
                self.window.grab_release()
            except tk.TclError:
                pass
            self._grabbed = False

        submenu._show_at(x, y)
        if focus_first:
            submenu._set_highlight_first()
            submenu.window.focus_force()
