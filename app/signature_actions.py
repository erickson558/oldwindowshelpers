"""Acción "Animar" del menú: cada personaje tiene un gesto/animación propia
que lo distingue de los demás (en vez de reproducir una animación al azar
como hace "Decime un consejo").

Los nombres de animación de acá SÍ existen en los agent.json reales (ver
tools/fetch_assets.py) — se eligieron a mano revisando qué tenía cada
personaje, priorizando lo que resulta más "de su personalidad":

- Clippy:  GetWizardy   -> el clip se transforma en mago, su gesto más icónico.
- F1:      GetTechy     -> encaja con su diseño de robot.
- Genius:  Congratulate -> un "¡Eureka!" celebratorio, a tono con Einstein.
- Links:   GetArtsy     -> el gato haciendo de artista.
- Merlin:  DoMagic1     -> animación EXCLUSIVA de Merlin (no la tiene ningún
                            otro personaje), un hechizo de mago de verdad.
- Rocky:   EmptyTrash   -> el perro escarbando en la basura, un chiste que
                            le queda perfecto a un personaje canino.
- MotherNature: Alert    -> un "aviso de la naturaleza", a tono con su mensaje
                            ambiental (ver locales/*.json -> animate.MotherNature).
- OfficeLogo:   Show     -> el logo "se presenta"; no tiene cara ni gestos
                            propios, así que la animación de aparición es lo
                            más "de su personalidad" que existe.
- Dot:          Explain  -> explica cambiando de forma, coherente con su frase
                            ("puedo ser la forma que quieras que sea").

Si se agrega un personaje nuevo sin entrada acá, `get_signature_animation`
cae de vuelta a una animación "one-shot" al azar (ver Assistant.one_shot_animations
en app/animation.py), así "Animar" nunca se rompe por un personaje nuevo.
"""

import random

SIGNATURE_ANIMATIONS: dict[str, str] = {
    "Clippy": "GetWizardy",
    "F1": "GetTechy",
    "Genius": "Congratulate",
    "Links": "GetArtsy",
    "Merlin": "DoMagic1",
    "Rocky": "EmptyTrash",
    "MotherNature": "Alert",
    "OfficeLogo": "Show",
    "Dot": "Explain",
}


def get_signature_animation(assistant) -> str:
    """Devuelve el nombre de animación "de firma" del personaje activo.

    `assistant` es una instancia de app.animation.Assistant. Si el personaje
    no tiene una entrada explícita en SIGNATURE_ANIMATIONS (por ejemplo, uno
    agregado a mano por el usuario), o la animación elegida no existe en su
    agent.json, se elige una animación one-shot al azar como respaldo.
    """
    preferred = SIGNATURE_ANIMATIONS.get(assistant.name)
    if preferred and preferred in assistant.animations:
        return preferred
    return random.choice(assistant.one_shot_animations())
