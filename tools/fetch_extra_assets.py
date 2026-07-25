"""Descarga y convierte los personajes "extra" de Office Assistant para los
que NO se consiguió un archivo .acs real (a diferencia de Mother Nature,
Office Logo y The Dot — ver tools/fetch_acs_assets.py, que sí tiene sus
animaciones completas y nombradas).

Scribble y Power Pup solo se consiguieron como un .zip de The Spriters
Resource con un PNG individual ya recortado por frame (sin agrupar por
animación, y con tamaño variable por frame). Se recomponen en un sprite
sheet nuevo, centrando cada frame horizontalmente y apoyándolo abajo dentro
de una celda de tamaño fijo (el máximo del personaje), y quedan con una
única animación "Idle" que reproduce todos sus frames en secuencia — menor
fidelidad que el resto del roster: no tienen "Wave"/"Greeting"/etc. por
separado, y por eso tampoco tienen entrada en app/signature_actions.py (usan
el resguardo automático: one-shot al azar, que en su caso es su única
animación "Idle"). Ver specs/SPEC.md 2.1/2.3b para más detalle y qué se
intentó para conseguirles animaciones completas también.

IMPORTANTE (ver NOTICE): igual que con tools/fetch_assets.py, el arte es
propiedad de Microsoft. A diferencia de clippy.js, The Spriters Resource
declara sus términos de uso como "solo para trabajos no comerciales / no
publicados" (https://www.spriters-resource.com/page/tou/) — subir esto a un
repositorio público excede literalmente ese "no publicado". Se documenta acá
y en NOTICE de forma explícita: es una decisión consciente del usuario
(igual criterio de riesgo aceptado que con los primeros 6 personajes), no un
descuido.

Uso:
    python tools/fetch_extra_assets.py
"""

import io
import json
import statistics
import sys
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

# Algunos ZIPs de The Spriters Resource traen, mezclado entre los frames
# normales, algún archivo suelto que no es un frame de animación real (ej. en
# Power Pup, frame_014.png mide 791x857 -- ~220x el área del resto -- casi
# seguro una captura de la ventana de "Gallery" colada por error durante la
# extracción). Si se usara tal cual, el frame_width/frame_height de todo el
# personaje (definidos como el máximo de todos los frames) se dispararía y
# generaría un sprite sheet gigantesco y con el personaje minúsculo en una
# esquina. Se descartan frames cuya área supere este múltiplo de la mediana.
OUTLIER_AREA_RATIO = 15

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "agents"

FRAMES_ZIP_CHARACTERS = {
    "Scribble": "https://www.spriters-resource.com/media/assets/504/522069.zip",
    "PowerPup": "https://www.spriters-resource.com/media/assets/504/522077.zip",
}

FRAME_DURATION_MS = 120


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _write_agent(name: str, frame_w: int, frame_h: int, sheet: Image.Image, positions: list) -> None:
    dest = ASSETS_DIR / name
    dest.mkdir(parents=True, exist_ok=True)
    sheet.save(dest / "map.png")
    agent = {
        "name": name,
        "sprite": "map.png",
        "frame_width": frame_w,
        "frame_height": frame_h,
        "animations": {
            "Idle": [
                {"duration": FRAME_DURATION_MS, "images": [[x, y]]} for x, y in positions
            ]
        },
    }
    (dest / "agent.json").write_text(
        json.dumps(agent, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  OK: {name} -> {len(positions)} frames (1 animacion: Idle)")


def fetch_frames_zip_character(name: str, url: str) -> None:
    print(f"Descargando {name} (zip de frames individuales)...")
    raw = _download(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = sorted(n for n in zf.namelist() if n.lower().endswith(".png"))
        frames = []
        for entry in names:
            with zf.open(entry) as f:
                img = Image.open(f)
                img.load()
                frames.append(img.convert("RGBA"))

    median_area = statistics.median(f.width * f.height for f in frames)
    kept = [f for f in frames if (f.width * f.height) <= median_area * OUTLIER_AREA_RATIO]
    dropped = len(frames) - len(kept)
    if dropped:
        print(f"  descartados {dropped} frame(s) atipico(s) (posible artefacto de extraccion)")
    frames = kept

    frame_w = max(f.width for f in frames)
    frame_h = max(f.height for f in frames)

    cols = 15
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * frame_h), (0, 0, 0, 0))

    positions = []
    for index, frame in enumerate(frames):
        col, row = index % cols, index // cols
        cell_x, cell_y = col * frame_w, row * frame_h
        # Cada frame original ya viene recortado a su propio contenido (tamaño
        # variable), así que lo centramos horizontalmente y lo apoyamos abajo
        # dentro de una celda de tamaño fijo (el máximo del personaje) — se
        # pierde la posición relativa exacta entre frames que tenía el sheet
        # original sin editar, pero es la única forma de reusar un motor de
        # animación de frame_width/height constante con esta fuente.
        paste_x = cell_x + (frame_w - frame.width) // 2
        paste_y = cell_y + (frame_h - frame.height)
        sheet.alpha_composite(frame, (paste_x, paste_y))
        positions.append((cell_x, cell_y))

    _write_agent(name, frame_w, frame_h, sheet, positions)


def main() -> int:
    for name, url in FRAMES_ZIP_CHARACTERS.items():
        fetch_frames_zip_character(name, url)
    print(f"\nListo. Personajes 'extra' generados en {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
