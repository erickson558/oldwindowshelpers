"""Declara el proceso como "DPI aware" ante Windows.

Sin esto, en pantallas modernas con escalado (125%/150%/200%, muy común en
laptops 1440p/4K), Windows trata a la app como si no supiera de DPI y la
escala él mismo estirando el bitmap final — el resultado se ve borroso y con
un tamaño distinto al que calculamos en app/animation.py (DISPLAY_HEIGHT deja
de ser el tamaño real en pantalla). Hay que llamarlo ANTES de crear cualquier
ventana de Tkinter.
"""

import ctypes


def make_process_dpi_aware() -> None:
    try:
        # PROCESS_SYSTEM_DPI_AWARE=1: la app se dibuja nítida según el DPI
        # del monitor principal, en vez de que Windows la estire después.
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # respaldo para Windows más viejo
        except (AttributeError, OSError):
            pass  # mejor arrancar sin DPI awareness que no arrancar
