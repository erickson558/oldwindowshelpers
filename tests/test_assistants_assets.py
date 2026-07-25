"""Valida que cada personaje descargado por tools/fetch_assets.py tenga
metadata consistente con su sprite sheet: si esto falla, animation.py va a
intentar recortar fuera de los límites de la imagen en tiempo real."""

import json

from app.animation import Assistant
from app.resources import resource_path


def test_at_least_one_character_available():
    assert Assistant.available(), (
        "No hay personajes en assets/agents/. Corré 'python tools/fetch_assets.py' primero."
    )


def test_every_character_metadata_matches_its_sprite_sheet():
    from PIL import Image

    for name in Assistant.available():
        agent_dir = resource_path("assets", "agents", name)
        meta = json.loads((agent_dir / "agent.json").read_text(encoding="utf-8"))
        sheet = Image.open(agent_dir / meta["sprite"])
        fw, fh = meta["frame_width"], meta["frame_height"]

        assert meta["animations"], f"{name}: no tiene animaciones"

        for anim_name, frames in meta["animations"].items():
            assert frames, f"{name}/{anim_name}: animación vacía"
            for frame in frames:
                for x, y in frame["images"]:
                    assert 0 <= x and x + fw <= sheet.width, (
                        f"{name}/{anim_name}: recorte X fuera de rango ({x}, ancho sheet {sheet.width})"
                    )
                    assert 0 <= y and y + fh <= sheet.height, (
                        f"{name}/{anim_name}: recorte Y fuera de rango ({y}, alto sheet {sheet.height})"
                    )
