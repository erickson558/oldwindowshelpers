"""Descarga y convierte los sprite sheets de los Ayudantes de Office clásicos
desde el proyecto open-source clippy.js (MIT), que ya extrajo y publica estos
assets de Microsoft Agent / Office Assistant hace más de una década.

Uso:
    python tools/fetch_assets.py            # descarga los 6 personajes por defecto
    python tools/fetch_assets.py Clippy Rocky

Convierte el formato original (clippy.ready('Nombre', {...json...})) a nuestro
esquema simplificado (agent.json) descrito en app/animation.py, y guarda el
sprite sheet como map.png junto a él.

IMPORTANTE (ver NOTICE): el código de este script es nuestro, pero el arte
descargado (map.png) es propiedad de Microsoft. Se incluye en el repo con
fines de preservación/nostalgia, no de uso comercial.
"""

import json
import sys
import urllib.request
from pathlib import Path

REPO_RAW = "https://raw.githubusercontent.com/clippyjs/clippy.js/master/agents"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "agents"

# Personajes que realmente formaron parte del "Office Assistant" clásico
# (Office 97/2000/XP/2003). Se excluyen a propósito del set completo de clippy.js:
#   - Bonzi: personaje de BONZI Software, una empresa distinta, no de Microsoft.
#   - Rover: es de Windows XP Search Companion, no del Office Assistant.
#   - Genie, Peedy: son demos de Microsoft Agent (otra tecnología), no aparecieron
#     nunca como Office Assistant dentro de Word/Excel/etc.
OFFICE_ASSISTANTS = ["Clippy", "F1", "Genius", "Links", "Merlin", "Rocky"]


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def _parse_agent_js(raw_js: bytes) -> dict:
    """El archivo original es JSONP: clippy.ready('Nombre', {...}) — extraemos el JSON."""
    text = raw_js.decode("utf-8")
    start = text.index("{")
    end = text.rindex("}")
    return json.loads(text[start : end + 1])


def _convert_animation(frames: list[dict]) -> list[dict]:
    """Algunos frames originales no traen "images" (son solo una pausa que
    sostiene la imagen anterior, o un punto de "branching" sin dibujo propio).
    Les copiamos las imágenes del frame previo dentro de la misma animación;
    si es el primer frame y no hay uno previo, usamos [[0, 0]] (la pose neutra
    de la esquina superior izquierda del sprite sheet) como respaldo seguro."""
    converted = []
    last_images = [[0, 0]]
    for frame in frames:
        images = frame.get("images", last_images)
        last_images = images
        converted.append({"duration": frame.get("duration", 100), "images": images})
    return converted


def _convert(original: dict, name: str) -> dict:
    """Se queda solo con lo que nuestro motor sabe reproducir (ver app/animation.py):
    tamaño de frame y animaciones con sus imágenes por frame. Se descartan los
    sonidos y las ramas (exitBranch/branching) de la máquina de estados original
    de Microsoft Agent — nuestro reproductor las ignora y toca todo en secuencia,
    lo cual simplifica el motor a cambio de perder algunas transiciones del
    original (limitación conocida y documentada en README/SPEC)."""
    frame_w, frame_h = original["framesize"]
    animations = {
        anim_name: _convert_animation(data["frames"])
        for anim_name, data in original["animations"].items()
    }
    return {
        "name": name,
        "sprite": "map.png",
        "frame_width": frame_w,
        "frame_height": frame_h,
        "animations": animations,
    }


def fetch_one(name: str) -> None:
    dest = ASSETS_DIR / name
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Descargando {name}...")
    agent_js = _download(f"{REPO_RAW}/{name}/agent.js")
    map_png = _download(f"{REPO_RAW}/{name}/map.png")

    original = _parse_agent_js(agent_js)
    converted = _convert(original, name)

    (dest / "agent.json").write_text(
        json.dumps(converted, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (dest / "map.png").write_bytes(map_png)
    print(f"  OK: {len(converted['animations'])} animaciones, sprite {len(map_png)} bytes")


def main(argv: list[str]) -> int:
    names = argv or OFFICE_ASSISTANTS
    failures = []
    for name in names:
        try:
            fetch_one(name)
        except Exception as exc:  # noqa: BLE001 - seguimos con el resto si uno falla
            failures.append(name)
            print(f"  FALLO {name}: {exc}")

    if failures:
        print(f"\nNo se pudieron descargar: {', '.join(failures)}.")
        print("Revisa tu conexion a internet y volve a correr el script.")
        return 1

    print(f"\nListo. {len(names)} personaje(s) en {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
