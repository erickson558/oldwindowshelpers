"""Acción "Ayuda de Windows" del menú: simula la tecla F1.

F1 es el atajo de ayuda contextual universal de Windows, sin cambios desde
Windows 95 hasta las versiones actuales — dejamos que sea el propio Windows (o
la app que tenga el foco en ese momento) quien decida qué mostrar, en vez de
intentar adivinar un ejecutable de ayuda específico por versión.
"""

import ctypes

VK_F1 = 0x70
KEYEVENTF_KEYUP = 0x0002


def trigger_windows_help() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_F1, 0, 0, 0)
    user32.keybd_event(VK_F1, 0, KEYEVENTF_KEYUP, 0)
