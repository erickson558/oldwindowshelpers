"""Valida que cada personaje descargado por tools/fetch_assets.py tenga
metadata consistente con su sprite sheet: si esto falla, animation.py va a
intentar recortar fuera de los límites de la imagen en tiempo real."""

import json

from app.animation import Assistant
from app.resources import resource_path

# Los 6 originales (tools/fetch_assets.py, formato clippy.js completo), los 4
# de alta fidelidad via .acs real (tools/fetch_acs_assets.py) y los 5 de
# fidelidad reducida (tools/fetch_extra_assets.py, "Idle" + "MotionNN" cortas
# — ver specs/SPEC.md). Si uno falta, esta prueba lo marca en vez de pasar en
# silencio con un roster incompleto.
EXPECTED_CHARACTERS = {
    "Clippy", "F1", "Genius", "Links", "Merlin", "Rocky",
    "MotherNature", "OfficeLogo", "Dot", "Kairu",
    "Scribble", "PowerPup", "Will", "SaekoSensei", "MonkeyKing",
}

# v0.4.0 tenía un bug real: "Transform" reproducía TODOS los frames de un
# personaje como un solo disparo -- para Saeko Sensei/Monkey King eran más de
# 2.5 MINUTOS (150s+) por click de "Animar", y si el usuario cambiaba de
# personaje antes de que terminara, quedaba "pegado" en un frame cualquiera
# del medio (ver specs/SPEC.md 2.3b). Entre los one-shots legítimos más
# largos del roster real (via .acs/clippy.js) está Rocky/Processing con
# 36.9s -- el límite de acá deja margen cómodo por encima de eso, pero sigue
# muy por debajo del rango del bug real (~150s+).
MAX_ONE_SHOT_DURATION_SECONDS = 60


def test_at_least_one_character_available():
    assert Assistant.available(), (
        "No hay personajes en assets/agents/. Corré 'python tools/fetch_assets.py' primero."
    )


def test_full_expected_roster_is_present():
    missing = EXPECTED_CHARACTERS - set(Assistant.available())
    assert not missing, (
        f"Faltan personajes esperados: {missing}. Corré tools/fetch_assets.py "
        "y/o tools/fetch_extra_assets.py."
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


def test_no_one_shot_animation_takes_absurdly_long_to_play():
    # Las animaciones "Idle" (loop continuo) SÍ pueden durar bastante --
    # loopean sin problema (ej. Clippy/IdleSnooze dura 13.6s, normal para un
    # loop). El límite solo aplica a los one-shots (el resto): esos se
    # disparan una vez por una acción del usuario y tienen que terminar
    # rápido, no quedar reproduciéndose varios minutos en segundo plano.
    for name in Assistant.available():
        agent_dir = resource_path("assets", "agents", name)
        meta = json.loads((agent_dir / "agent.json").read_text(encoding="utf-8"))
        for anim_name, frames in meta["animations"].items():
            if "idle" in anim_name.lower():
                continue
            duration_seconds = sum(f.get("duration", 100) for f in frames) / 1000
            assert duration_seconds <= MAX_ONE_SHOT_DURATION_SECONDS, (
                f"{name}/{anim_name} dura {duration_seconds:.1f}s (máximo "
                f"{MAX_ONE_SHOT_DURATION_SECONDS}s) — ver el bug de v0.4.0 en "
                "specs/SPEC.md 2.3b antes de subir este límite."
            )
