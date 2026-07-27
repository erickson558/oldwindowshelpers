"""Descarga y convierte los personajes "extra" de Office Assistant para los
que NO se consiguió un archivo .acs real (a diferencia de Mother Nature,
Office Logo, The Dot y Kairu — ver tools/fetch_acs_assets.py, que sí tienen
sus animaciones completas y nombradas).

Scribble, Power Pup, Will, Saeko Sensei y Monkey King solo se consiguieron
como un .zip de The Spriters Resource con un PNG individual ya recortado por
frame — sin agrupar por animación, y con tamaño variable por frame (cada uno
recortado a su propio contenido). Se recomponen en un sprite sheet nuevo,
centrando cada frame (horizontal Y vertical) dentro de una celda de tamaño
fijo (el máximo del personaje, sin contar valores atípicos).

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
en vez de un collage. El bloque elegido como "Idle" (loop por defecto) es
el que gana un puntaje que combina área promedio ALTA (pose reconocible,
no un recorte chico de transición) con variación de tamaño interna BAJA
entre sus propios frames (ver v0.5.1 más abajo); el resto quedan como
one-shots — "Decime un consejo" y "Animar" eligen uno al azar entre ellos,
así se recupera la variedad de "animaciones random" que tienen el resto de
los personajes.

v0.5.1 (bugfix, ver specs/SPEC.md 2.3b): reportado que Will/Saeko
Sensei/Power Pup "se ven animados cuando cargan, no estables" incluso en su
loop "Idle" calmo. Tres causas raíz encontradas, las tres en este archivo:

1. El chunk "Idle" se elegía por MAYOR ÁREA PROMEDIO nomás, sin mirar cuánto
   variaba el tamaño de un frame al siguiente DENTRO de ese mismo chunk —
   Power Pup tenía un chunk "Idle" cuyos frames iban de 744px² a 28026px²
   (37x de diferencia), Will de 3895 a 35840 (9x). En loop continuo, eso se
   ve exactamente como estar a mitad de una transformación, no como un
   personaje descansando. Se corrige en `_select_idle_chunk_index`, que
   ahora penaliza la variación interna (coeficiente de variación) además de
   premiar el área promedio.
2. Cada frame se apoyaba abajo ("bottom-anchor") dentro de su celda de
   tamaño fijo, así que un frame chico y uno grande consecutivos también
   saltaban de posición vertical, no solo de tamaño. Se corrige centrando el
   paste en AMBOS ejes en vez de apoyarlo abajo.
3. La más sutil: el "área" de cada frame se medía como `ancho * alto` del
   PNG individual tal cual venía en el .zip de origen. Eso asume que la
   fuente ya recorta cada frame a su contenido real — cierto para Will,
   Power Pup y Scribble, pero investigando el bug se encontró que **Saeko
   Sensei y Monkey King NO vienen recortados así**: sus ~1300 frames
   comparten EXACTAMENTE el mismo lienzo nominal (ej. 11270px² para los
   1323 frames de Saeko Sensei), aunque el personaje dibujado adentro varíe
   muchísimo de tamaño real (812px² a 9800px² de contenido visible medido
   por bounding box del alfa). Con esa fuente, `ancho * alto` es una
   constante sin ningún poder de distinguir un frame grande de uno chico —
   tanto el filtro de valores atípicos como la selección de "Idle" quedaban
   ciegos para estos dos personajes. Se corrige con `_tight_area()`, que
   mide el bounding box real del canal alfa en vez del lienzo nominal —
   funciona igual de bien para fuentes ya recortadas (da prácticamente el
   mismo número) y es lo único que funciona para fuentes sin recortar.

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


def _tight_area(img: Image.Image) -> int:
    """Área del contenido visible real (bounding box del canal alfa), NO del
    lienzo nominal del PNG (`img.width * img.height`). Se descubrió durante
    el fix de v0.5.1 que algunas fuentes (Saeko Sensei, Monkey King) traen
    CADA frame ya pre-pegado en un lienzo de tamaño fijo sin recortar --
    ancho*alto da el MISMO número para los 1300+ frames del personaje, así
    que no sirve para distinguir una pose grande de una chica. El bounding
    box del alfa sí refleja cuánto ocupa el personaje en pantalla en ese
    frame puntual, sea la fuente pre-recortada (Will/Power Pup/Scribble) o
    no (Saeko Sensei/Monkey King)."""
    bbox = img.split()[-1].getbbox()
    if bbox is None:
        return 0
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


# Un chunk candidato a "Idle" tiene que representar una pose de tamaño
# razonable -- se descarta cualquier chunk cuya área promedio quede por
# debajo de esta fracción del área promedio del chunk MÁS GRANDE del
# personaje (no de la mediana: verificado en vivo -- ver v0.5.1 en el
# docstring del módulo -- que con un piso relativo a la mediana, algunos
# personajes elegían un chunk perfectamente ESTABLE pero que en pantalla
# era solo un fragmento pequeño sin relación reconocible con el personaje,
# ej. Power Pup mostrando apenas un boomerang blanco suelto en vez de su
# pose de pie). Entre los chunks que sí llegan a este piso de tamaño, gana
# el más ESTABLE (menor coeficiente de variación), no el de mayor área --
# premiar área por sobre estabilidad es lo que dejaba elegir chunks con 37x
# de diferencia entre su frame más chico y más grande dentro del mismo
# chunk.
IDLE_MIN_AREA_RATIO = 0.65


def _select_idle_chunk_index(area_chunks: list) -> int:
    """Elige qué bloque de frames se usa como "Idle" (el loop calmo por
    defecto): el más ESTABLE (menor variación de tamaño interna) entre los
    que tienen un área promedio razonable, no el de mayor área promedio a
    secas. Un bloque puede promediar grande y aun así mezclar un frame
    minúsculo (transición) con uno enorme (pose completa) -- en loop
    continuo eso se ve como si el personaje estuviera constantemente a
    mitad de una transformación, no descansando (ver v0.5.1 en el docstring
    del módulo)."""
    def stats(chunk):
        mean = sum(chunk) / len(chunk)
        variance = sum((area - mean) ** 2 for area in chunk) / len(chunk)
        coefficient_of_variation = (variance ** 0.5 / mean) if mean else 0.0
        return mean, coefficient_of_variation

    chunk_stats = [stats(chunk) for chunk in area_chunks]
    largest_mean_area = max(mean for mean, _cv in chunk_stats)
    area_floor = largest_mean_area * IDLE_MIN_AREA_RATIO

    candidates = [i for i, (mean, _cv) in enumerate(chunk_stats) if mean >= area_floor]
    return min(candidates, key=lambda i: chunk_stats[i][1])


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
    median_area = statistics.median(_tight_area(f) for f in frames)
    frames = [f for f in frames if _tight_area(f) <= median_area * OUTLIER_AREA_RATIO]
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
        # variable), así que lo centramos en AMBOS ejes dentro de una celda de
        # tamaño fijo (el máximo del personaje) — se pierde la posición
        # relativa exacta entre frames que tenía el sheet original sin editar,
        # pero es la única forma de reusar un motor de animación de
        # frame_width/height constante con esta fuente. Centrar en vez de
        # apoyar abajo evita que un frame chico y uno grande consecutivos
        # salten de posición vertical además de tamaño (v0.5.1: ver docstring
        # del módulo, esa combinación era parte del "se ve inestable").
        paste_x = cell_x + (frame_w - frame.width) // 2
        paste_y = cell_y + (frame_h - frame.height) // 2
        sheet.alpha_composite(frame, (paste_x, paste_y))
        positions.append((cell_x, cell_y))
        areas.append(_tight_area(frame))

    # Partir en bloques CONSECUTIVOS (no reordenados por área) de CHUNK_SIZE:
    # frames vecinos en el material original tienen mucha más chance de
    # pertenecer al mismo gesto real que frames sueltos elegidos por tamaño.
    position_chunks = [positions[i : i + CHUNK_SIZE] for i in range(0, len(positions), CHUNK_SIZE)]
    area_chunks = [areas[i : i + CHUNK_SIZE] for i in range(0, len(areas), CHUNK_SIZE)]
    idle_chunk_index = _select_idle_chunk_index(area_chunks)

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
