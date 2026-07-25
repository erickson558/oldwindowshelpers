"""Motor de animación: lee un sprite sheet + metadata JSON y entrega frames listos
para dibujar en pantalla (PhotoImage de Tkinter).

Formato esperado en assets/agents/<Nombre>/agent.json (generado por
tools/fetch_assets.py a partir de los datos originales de Microsoft Agent /
Office Assistant que trae el proyecto open-source clippy.js):

{
  "name": "Clippy",
  "sprite": "map.png",
  "frame_width": 124,
  "frame_height": 93,
  "animations": {
    "Idle1_1": [{"duration": 100, "images": [[0, 0]]}, ...],
    "Greeting": [...],
    ...
  }
}

Cada frame tiene una lista "images" (una por capa/overlay) con offsets [x, y] en
píxeles dentro del sprite sheet; se recortan y se componen en orden. No se
replica la máquina de estados original de Microsoft Agent (exitBranch/sonidos):
para un desktop pet alcanza con reproducir cada animación en secuencia lineal,
lo cual simplifica muchísimo el motor a cambio de perder algunas transiciones
"inteligentes" del original (documentado como limitación conocida).
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageTk

from .resources import resource_path

AGENTS_DIR = "assets/agents"

# Altura de pantalla "cómoda" a la que se escala TODO personaje al dibujarlo,
# sin importar el tamaño original de su sprite sheet. Los 6 personajes de
# clippy.js miden ~93-128px de alto y los 5 de fidelidad reducida entre 203 y
# 285px — sin esto, cambiar de personaje pega un salto de tamaño brusco e
# incómodo en pantallas modernas. Se preserva el aspect ratio de cada uno.
DISPLAY_HEIGHT = 160

# Por debajo de este valor de alfa, el píxel se vuelve 100% transparente; por
# encima, 100% opaco. Es necesario "endurecer" así el canal alfa porque la
# transparencia por color llave de Tkinter (ver app/character_window.py) NO
# hace blending real: un píxel semitransparente del PNG original (los bordes
# suavizados/antialiased de cualquier dibujo) se termina mezclando con el
# fondo mágenta del widget ANTES de que el color-key lo recorte, dejando un
# halo rosa/mágenta visible alrededor de cada personaje. Binarizar el alfa
# elimina ese halo a cambio de un borde levemente menos suave — es el
# trade-off estándar de esta técnica de transparencia.
ALPHA_HARDEN_THRESHOLD = 140


def _harden_alpha(image: Image.Image, threshold: int = ALPHA_HARDEN_THRESHOLD) -> Image.Image:
    r, g, b, a = image.split()
    a = a.point(lambda p: 255 if p >= threshold else 0)
    return Image.merge("RGBA", (r, g, b, a))


class Assistant:
    """Un personaje cargado: su sprite sheet completo más el índice de animaciones."""

    def __init__(self, name: str):
        self.name = name
        agent_dir = resource_path(AGENTS_DIR, name)
        with open(agent_dir / "agent.json", encoding="utf-8") as f:
            meta = json.load(f)
        self.frame_width: int = meta["frame_width"]
        self.frame_height: int = meta["frame_height"]
        self.animations: dict[str, list[dict]] = meta["animations"]
        self.sheet = Image.open(agent_dir / meta["sprite"]).convert("RGBA")
        self._frame_cache: dict[tuple[str, int], ImageTk.PhotoImage] = {}

        # Tamaño de despliegue: mismo alto "cómodo" para todos los personajes,
        # ancho proporcional al aspect ratio real de cada uno.
        scale = DISPLAY_HEIGHT / self.frame_height
        self.display_width = max(1, round(self.frame_width * scale))
        self.display_height = DISPLAY_HEIGHT

    @staticmethod
    def available() -> list[str]:
        """Nombres de personajes disponibles (carpetas con agent.json bajo assets/agents)."""
        base = resource_path(AGENTS_DIR)
        if not base.exists():
            return []
        return sorted(
            p.name for p in base.iterdir() if p.is_dir() and (p / "agent.json").exists()
        )

    def idle_animations(self) -> list[str]:
        idle = [name for name in self.animations if "idle" in name.lower()]
        return idle or list(self.animations.keys())[:1]

    def pick_idle_animation(self) -> str:
        return random.choice(self.idle_animations())

    def one_shot_animations(self) -> list[str]:
        """Animaciones no-idle, usadas para "decir un consejo" / gestos al azar."""
        candidates = [name for name in self.animations if "idle" not in name.lower()]
        return candidates or list(self.animations.keys())

    def frame_image(self, animation: str, index: int) -> ImageTk.PhotoImage:
        cache_key = (animation, index)
        if cache_key in self._frame_cache:
            return self._frame_cache[cache_key]

        frame = self.animations[animation][index]
        composed = Image.new("RGBA", (self.frame_width, self.frame_height), (0, 0, 0, 0))
        for x, y in frame["images"]:
            box = (x, y, x + self.frame_width, y + self.frame_height)
            layer = self.sheet.crop(box)
            composed.alpha_composite(layer)

        composed = composed.resize(
            (self.display_width, self.display_height), Image.LANCZOS
        )
        # El resize reintroduce bordes semitransparentes (por el propio
        # remuestreo) aunque el sheet original ya viniera con alfa binario,
        # así que se vuelve a endurecer el alfa DESPUÉS de escalar — si se
        # hiciera antes, el resize lo deshace.
        composed = _harden_alpha(composed)

        photo = ImageTk.PhotoImage(composed)
        self._frame_cache[cache_key] = photo
        return photo

    def frame_duration_ms(self, animation: str, index: int) -> int:
        return self.animations[animation][index].get("duration", 100)

    def frame_count(self, animation: str) -> int:
        return len(self.animations[animation])
