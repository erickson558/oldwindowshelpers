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

        photo = ImageTk.PhotoImage(composed)
        self._frame_cache[cache_key] = photo
        return photo

    def frame_duration_ms(self, animation: str, index: int) -> int:
        return self.animations[animation][index].get("duration", 100)

    def frame_count(self, animation: str) -> int:
        return len(self.animations[animation])
