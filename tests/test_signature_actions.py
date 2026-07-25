"""Si SIGNATURE_ANIMATIONS apunta a un nombre de animación que no existe
(por un typo, o porque cambió el set de animaciones al re-descargar assets),
"Animar" rompería en tiempo real. Estas pruebas lo detectan antes de eso."""

from app.animation import Assistant
from app.signature_actions import SIGNATURE_ANIMATIONS, get_signature_animation


def test_every_declared_signature_animation_exists_in_its_character():
    for name, animation in SIGNATURE_ANIMATIONS.items():
        if name not in Assistant.available():
            continue  # personaje no instalado en este entorno; no hay nada que validar
        assistant = Assistant(name)
        assert animation in assistant.animations, (
            f"{name}: la animacion de firma '{animation}' no existe en su agent.json"
        )


def test_get_signature_animation_returns_a_playable_animation_for_every_character():
    for name in Assistant.available():
        assistant = Assistant(name)
        animation = get_signature_animation(assistant)
        assert animation in assistant.animations, (
            f"{name}: get_signature_animation devolvio '{animation}', que no existe"
        )
