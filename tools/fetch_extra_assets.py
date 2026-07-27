"""Descarga y convierte los personajes "extra" de Office Assistant para los
que NO se consiguió un archivo .acs real (a diferencia de Mother Nature,
Office Logo, The Dot y Kairu — ver tools/fetch_acs_assets.py, que sí tienen
sus animaciones completas y nombradas).

Scribble, Power Pup, Will, Saeko Sensei y Monkey King solo se consiguieron
como un .zip de The Spriters Resource con un PNG individual ya recortado por
frame — sin agrupar por animación, y con tamaño variable por frame (cada uno
recortado a su propio contenido). Se recomponen en un sprite sheet nuevo,
centrando cada frame horizontalmente y apoyándolo abajo dentro de una celda
de tamaño fijo (el máximo del personaje, sin contar valores atípicos).

Cómo se arman las animaciones (v0.5.0, reemplaza al esquema Idle/Transform
de v0.4.0 — ver por qué en specs/SPEC.md 2.3b):

Como no sabemos qué frames formaban qué animación con nombre, la v0.4.0
probó con solo dos animaciones: "Idle" (frames grandes sueltos, cherry-
picked de cualquier punto de la secuencia) y "Transform" (¡la secuencia
COMPLETA como un solo disparo!). Eso resultó en dos problemas reales,
reportados por el usuario y confirmados: (1) el loop de "Idle" saltaba
entre poses sin relación (elegidas por área, no por cercanía en la
secuencia original), y se veía como una sucesión de cortes en vez de una
animación fluida; (2) "Transform" reproducía TODOS los frames del personaje
de una — para Saeko Sensei/Monkey King (~1300 frames a 120ms) eso son
¡más de 2 minutos y medio! Si el usuario cambiaba de personaje o hacía
cualquier otra cosa antes de que terminara, al volver lo encontraba
congelado en un frame cualquiera del medio — exactamente el "se ve a media
animación" que se reportó.

La solución: partir la secuencia (ya en su orden original, sin reordenar
por área) en bloques CONSECUTIVOS de `CHUNK_SIZE` frames, cada uno una
animación nombrada "MotionNN" de pocos segundos de largo. Frames
consecutivos en el material original tienen mucha más chance de pertenecer
al mismo gesto real que frames elegidos por área de cualquier punto de la
secuencia, así que cada bloque se ve como una animación corta con sentido
en vez de un collage. El bloque con mayor área promedio (más chance de ser
"personaje de cuerpo casi completo") se renombra "Idle" y es el que hace
loop por defecto; el resto quedan como one-shots — "Decime un consejo" y
"Animar" eligen uno al azar entre ellos, así se recupera la variedad de
"animaciones random" que tienen el resto de los personajes.

Ver specs/SPEC.md 2.1/2.3b para más detalle, y qué se intentó para
conseguirles animaciones completas y nombradas también (ninguno de estos 5
tiene su .acs encontrado pese a buscarlo en varias sesiones).

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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "agents"

# Algunos ZIPs de The Spriters Resource traen, mezclado entre los frames
# normales, algún archivo suelto que no es un frame de animación real (ej. en
# Power Pup, frame_014.png mide 791x857 -- ~220x el área del resto -- casi
# seguro una captura de la ventana de "Gallery" colada por error durante la
# extracción). Si se usara tal cual, el frame_width/frame_height de todo el
# personaje (definidos como el máximo de todos los frames) se dispararía y
# generaría un sprite sheet gigantesco y con el personaje minúsculo en una
# esquina. Se descartan frames cuya área supere este múltiplo de la mediana.
OUTLIER_AREA_RATIO = 15

# Algunos ZIPs traen, colado entre los frames reales, algún ícono/miniatura
# promocional de fondo sólido (encontrado en Scribble: un ícono de "cara de
# gato" y una miniatura de modelo 3D en wireframe — ninguno es un frame de
# animación real). Un frame de personaje real es una silueta recortada:
# tiene esquinas/bordes transparentes. Una miniatura rectangular casi no
# tiene transparencia. Se descartan frames cuyo relleno opaco supere esta
# fracción de su propio rectángulo.
MAX_OPAQUE_FILL_RATIO = 0.85

# Algunos personajes (Saeko Sensei, Monkey King) vienen en modo paleta sin
# canal alfa real: el "fondo" no es transparente, es un color mágenta sólido
# — el mismo color llave que ya usa esta app (ver TRANSPARENT_KEY en
# app/character_window.py) para su propio truco de transparencia. Sin
# convertirlo, se verían como un rectángulo mágenta opaco en vez de la
# silueta del personaje.
MAGENTA_KEY = (255, 0, 255)

# Cuántos frames CONSECUTIVOS (en el orden original) forman cada animación
# nombrada "MotionNN". A FRAME_DURATION_MS=120, 16 frames son ~1.9s -- un
# gesto de duración parecida a los one-shots de los personajes de alta
# fidelidad, ni tan corto que no se note ni tan largo que se sienta
# "trabado" si el usuario hace otra cosa mientras tanto (ver docstring del
# módulo: el bug real que esto reemplaza era una sola animación de HASTA
# 2.6 MINUTOS).
CHUNK_SIZE = 16

FRAMES_ZIP_CHARACTERS = {
    "Scribble": "https://www.spriters-resource.com/media/assets/504/522069.zip",
    "PowerPup": "https://www.spriters-resource.com/media/assets/504/522077.zip",
    "Will": "https://www.spriters-resource.com/media/assets/504/522085.zip",
    "SaekoSensei": "https://www.spriters-resource.com/media/assets/156/159613.zip",
    "MonkeyKing": "https://www.spriters-resource.com/media/assets/156/159371.zip",
}

FRAME_DURATION_MS = 120


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _magenta_to_real_alpha(img: Image.Image) -> Image.Image:
    """Si la imagen no trae transparencia real (fondo mágenta opaco en vez de
    alfa), la convierte. Si YA tiene transparencia real, no cambia nada
    (asumiendo que el arte del personaje en sí no usa mágenta puro — cierto
    en la práctica para estos personajes de dibujo tipo cartoon)."""
    rgba = img.convert("RGBA")
    pixels = rgba.getdata()
    new_pixels = [(0, 0, 0, 0) if p[:3] == MAGENTA_KEY and p[3] > 0 else p for p in pixels]
    rgba.putdata(new_pixels)
    return rgba


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
                frames.append(_magenta_to_real_alpha(img))

    def opaque_fill_ratio(img: Image.Image) -> float:
        alpha = img.split()[-1]
        opaque = sum(1 for a in alpha.getdata() if a > 200)
        return opaque / (img.width * img.height)

    before_junk_filter = len(frames)
    non_junk = [f for f in frames if opaque_fill_ratio(f) <= MAX_OPAQUE_FILL_RATIO]
    if non_junk:
        frames = non_junk
        dropped_junk = before_junk_filter - len(frames)
        if dropped_junk:
            print(f"  descartados {dropped_junk} frame(s) sin transparencia (icono/miniatura, no es un frame real)")
    else:
        # Algunos personajes (ej. Saeko Sensei) vienen exportados sin canal
        # alfa real (paleta sin transparencia) -- CADA frame da 100% opaco,
        # así que el filtro no aplica acá: no es que todo el personaje sea
        # basura, es que esta fuente en particular no usa transparencia.
        print("  (fuente sin transparencia real: se omite el filtro de icono/miniatura)")

    before_outlier_filter = len(frames)
    median_area = statistics.median(f.width * f.height for f in frames)
    frames = [f for f in frames if (f.width * f.height) <= median_area * OUTLIER_AREA_RATIO]
    dropped_outliers = before_outlier_filter - len(frames)
    if dropped_outliers:
        print(f"  descartados {dropped_outliers} frame(s) atipico(s) (posible artefacto de extraccion)")

    frame_w = max(f.width for f in frames)
    frame_h = max(f.height for f in frames)

    cols = 15
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * frame_h), (0, 0, 0, 0))

    positions = []
    areas = []
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
        areas.append(frame.width * frame.height)

    # Partir en bloques CONSECUTIVOS (no reordenados por área) de CHUNK_SIZE:
    # frames vecinos en el material original tienen mucha más chance de
    # pertenecer al mismo gesto real que frames sueltos elegidos por tamaño.
    position_chunks = [positions[i : i + CHUNK_SIZE] for i in range(0, len(positions), CHUNK_SIZE)]
    area_chunks = [areas[i : i + CHUNK_SIZE] for i in range(0, len(areas), CHUNK_SIZE)]
    avg_area_per_chunk = [sum(chunk) / len(chunk) for chunk in area_chunks]
    idle_chunk_index = avg_area_per_chunk.index(max(avg_area_per_chunk))

    animations = {}
    for i, chunk in enumerate(position_chunks):
        anim_name = "Idle" if i == idle_chunk_index else f"Motion{i + 1:02d}"
        animations[anim_name] = [
            {"duration": FRAME_DURATION_MS, "images": [[x, y]]} for x, y in chunk
        ]

    dest = ASSETS_DIR / name
    dest.mkdir(parents=True, exist_ok=True)
    sheet.save(dest / "map.png")
    agent = {
        "name": name,
        "sprite": "map.png",
        "frame_width": frame_w,
        "frame_height": frame_h,
        "animations": animations,
    }
    (dest / "agent.json").write_text(
        json.dumps(agent, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    one_shot_count = len(animations) - 1
    print(
        f"  OK: {name} -> {len(animations)} animaciones "
        f"(1 Idle + {one_shot_count} one-shots de ~{CHUNK_SIZE * FRAME_DURATION_MS / 1000:.1f}s cada una)"
    )


def main() -> int:
    for name, url in FRAMES_ZIP_CHARACTERS.items():
        fetch_frames_zip_character(name, url)
    print(f"\nListo. Personajes 'extra' generados en {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
