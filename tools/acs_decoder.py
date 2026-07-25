"""Decodificador real del formato binario Microsoft Agent Character (.ACS) —
el mismo formato que Office 97/2000/XP usaba para Clippy, Merlín, Mother
Nature, etc. antes de que existiera clippy.js.

Este módulo es lo que le faltaba al importador de tools/acs_importer.py
(que hasta la versión anterior solo podía "detectar" un .acs, no leerlo de
verdad) y es lo que usa tools/fetch_acs_assets.py para regenerar Mother
Nature/Office Logo/The Dot. Se llegó a esta implementación investigando
primero (no adivinando):

- La "MSAgent Character Data Specification" (Lebeau Software, v1.3), la
  referencia no-oficial más citada del formato.
- El código fuente real de Double Agent (Cinnamon Software, GPLv3), un
  reproductor de Microsoft Agent de código abierto y ~15 años de vida que
  todavía hoy sabe leer estos archivos — en particular su descompresor
  (Core/AgentFileBinary.cpp::DecodeData).
- MSAgentUtils (tkfoss, Swift, CC0), una reimplementación independiente
  desde cero que llega exactamente a las mismas constantes de bajo nivel.

Las tres fuentes coinciden byte a byte en el contenedor y en el compresor
LZ propietario, lo cual le da mucha confianza a esta implementación aunque
no exista un spec oficial de Microsoft. Verificado en la práctica contra
tres archivos .acs reales (DOT.ACS, MNATURE.ACS, LOGO.ACS, obtenidos de
https://archive.org/details/binder-97-office972000assistants): las 112
animaciones (3589 frames) y las 1697 imágenes de esos tres archivos
decodifican al 100%, sin un solo frame corrupto ni truncado.

Qué NO se interpreta (documentado, no relevante para nuestro uso):
- El checksum por imagen/audio: el propio spec dice que el algoritmo nunca
  se determinó, y no hace falta para decodificar píxeles.
- Los datos de audio (siempre WAV sin comprimir): no nos interesan, esta
  app no reproduce sonido (ver specs/SPEC.md 2.3, limitación deliberada).
- La máscara de "región" (hit-testing) de cada imagen: no la necesitamos,
  usamos el índice de color transparente para la transparencia, igual que
  el resto de los personajes de este proyecto.
"""

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path


class AcsParseError(Exception):
    """El archivo no tiene la firma esperada o algo no calza con el formato."""


MAGIC = 0xABCDABC3


def _read_string(data: bytes, offset: int) -> tuple[str, int]:
    """STRING = ULONG cantidad_de_chars; WCHAR[cantidad] (UTF-16LE); WCHAR nulo final.

    Así es como los nombres de animación (RESTPOSE, WAVE, CONGRATULATE...)
    terminan siendo texto UTF-16LE plano dentro de un archivo binario: el
    contador es binario, pero el contenido en sí es texto sin comprimir.
    """
    (count,) = struct.unpack_from("<I", data, offset)
    offset += 4
    if count == 0:
        return "", offset
    n_bytes = count * 2
    text = data[offset : offset + n_bytes].decode("utf-16-le", errors="replace")
    offset += n_bytes + 2  # +2 por el WCHAR nulo final
    return text, offset


def _read_locator(data: bytes, offset: int) -> tuple[int, int, int]:
    """ACSLOCATOR = { ULONG offset_absoluto; ULONG tamaño_en_bytes }."""
    loc_offset, loc_size = struct.unpack_from("<II", data, offset)
    return loc_offset, loc_size, offset + 8


class _BitReader:
    """Lee bits desde el byte menos significativo, en ventanas de 32 bits —
    así es como tanto Double Agent como MSAgentUtils leen el bitstream
    comprimido (confirmado comparando ambas implementaciones byte a byte)."""

    def __init__(self, buf: bytes):
        self.buf = buf
        self.byte_pos = 0
        self.bit_pos = 0

    def _word(self) -> int:
        chunk = self.buf[self.byte_pos : self.byte_pos + 4]
        chunk = chunk + b"\x00" * (4 - len(chunk))
        return struct.unpack("<I", chunk)[0]

    def read_bits(self, n: int) -> int:
        result = 0
        got = 0
        while got < n:
            word = self._word()
            available = 32 - self.bit_pos
            take = min(n - got, available)
            bits = (word >> self.bit_pos) & ((1 << take) - 1)
            result |= bits << got
            got += take
            self.bit_pos += take
            if self.bit_pos >= 8:
                advance = self.bit_pos // 8
                self.byte_pos += advance
                self.bit_pos -= advance * 8
        return result

    def read_bit(self) -> int:
        return self.read_bits(1)


# (ancho_en_bits, valor_base, sumando_de_largo_de_corrida) por cada uno de los
# 4 "niveles" de offset — el nivel se elige contando cuántos 1s consecutivos
# preceden al valor (0, 10, 110, 111). El tercer campo (sumando) es el quirk
# que Double Agent aplica SOLO en el nivel de 20 bits (offsets grandes): se le
# suma 2 en vez de 1 al largo de la corrida. Encontrado leyendo el C++ real,
# no está claro en ninguna descripción escrita del formato.
_OFFSET_TIERS = [
    (6, 1, 1),
    (9, 65, 1),
    (12, 577, 1),
    (20, 4673, 2),
]


def decompress(stream: bytes, expected_size: int) -> bytes:
    """Descomprime el códec LZ propietario de Microsoft Agent (usado para los
    píxeles de cada imagen). Formato del stream: 1 byte 0x00 de cabecera,
    el bitstream comprimido, y 6 bytes 0xFF de relleno/centinela al final.

    Es un LZSS con dos particularidades no estándar, ambas verificadas contra
    el descompresor real de Double Agent y contra un ejemplo trabajado a mano
    en el spec de Lebeau (que se usa como caso de prueba, ver tests/):
      1. El offset se codifica en uno de 4 "niveles" (6/9/12/20 bits), elegido
         por un prefijo unario de hasta 3 unos.
      2. El largo de la corrida usa un prefijo unario de hasta 11 unos —a
         diferencia del prefijo de offset, este SIEMPRE consume un bit
         terminador, incluso al llegar al tope de 11 unos. Ese caso límite es
         fácil de pasar por alto (un desarrollador anterior probando esto
         mismo se equivocó ahí, causando que la imagen se corte a mitad de
         camino) — por eso el bloque `while/else` de abajo.
    """
    if len(stream) < 2:
        return b""
    if stream[0] != 0x00:
        raise AcsParseError(f"cabecera de stream comprimido inesperada: {stream[0]:#x}")

    reader = _BitReader(stream[1:])
    out = bytearray()

    while len(out) < expected_size:
        if reader.read_bit() == 0:
            out.append(reader.read_bits(8))
            continue

        ones = 0
        while ones < 3 and reader.read_bit() == 1:
            ones += 1
        bit_width, base_add, run_addend = _OFFSET_TIERS[ones]
        value = reader.read_bits(bit_width)
        if bit_width == 20 and value == 0x000FFFFF:
            break  # marca de fin de stream
        offset = value + base_add

        run_ones = 0
        while run_ones < 11:
            if reader.read_bit() == 1:
                run_ones += 1
            else:
                break
        else:
            reader.read_bit()  # el prefijo SIEMPRE consume un terminador, incluso en el tope
        suffix = reader.read_bits(run_ones) if run_ones else 0
        run_length = (1 << run_ones) + suffix + run_addend

        if offset > len(out):
            raise AcsParseError(f"referencia hacia atrás ({offset}) más grande que lo ya generado")
        remaining = expected_size - len(out)
        run_length = min(run_length, remaining)
        for _ in range(run_length):
            out.append(out[-offset])

    return bytes(out)


@dataclass
class AcsFrame:
    # Cada entrada es (índice_de_imagen, x, y). En los tres archivos que
    # probamos, x=y=0 siempre (cada imagen ya mide exactamente el canvas
    # completo) — igual soportamos offsets distintos de cero por si un
    # personaje futuro los usara.
    images: list[tuple[int, int, int]]
    duration_ms: int


@dataclass
class AcsAnimation:
    name: str
    frames: list[AcsFrame] = field(default_factory=list)


class AcsCharacter:
    """Personaje completo ya decodificado: tamaño de canvas, la lista de
    imágenes individuales ya convertidas a RGBA (`images`, indexada igual que
    en el archivo original — varias animaciones reutilizan la misma imagen,
    ej. "ojos cerrados", así que conviene no recomponerla cada vez) y todas
    las animaciones con sus frames (cada frame referencia una o más de esas
    imágenes por índice, ver AcsFrame)."""

    def __init__(self, canvas_width: int, canvas_height: int):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.images: list = []  # se completa en parse_acs_file(); PIL.Image.Image por índice
        self.animations: list[AcsAnimation] = []


def _decode_indexed_image(pixel_bytes: bytes, compressed: bool, width: int, height: int) -> bytes:
    """Devuelve los bytes crudos (índices de paleta, 1 byte/píxel) de una
    imagen, del tamaño exacto stride*height (stride = ancho alineado a 4
    bytes, como cualquier DIB de Windows)."""
    stride = (width + 3) & ~3
    expected = stride * height
    if not compressed:
        return pixel_bytes[:expected]
    return decompress(pixel_bytes, expected)


def _indexed_to_rgba(pixels: bytes, width: int, height: int, palette: list[tuple[int, int, int]], transparent_index: int):
    """Convierte píxeles indexados (DIB de abajo hacia arriba, como todo
    bitmap de Windows) a una imagen PIL RGBA de arriba hacia abajo."""
    from PIL import Image

    stride = (width + 3) & ~3
    img = Image.new("RGBA", (width, height))
    out_pixels = img.load()
    for y in range(height):
        src_row = height - 1 - y  # el DIB viene "boca abajo"
        row_start = src_row * stride
        row = pixels[row_start : row_start + width]
        for x, idx in enumerate(row):
            if idx == transparent_index:
                out_pixels[x, y] = (0, 0, 0, 0)
            else:
                r, g, b = palette[idx] if idx < len(palette) else (255, 0, 255)
                out_pixels[x, y] = (r, g, b, 255)
    return img


def parse_acs_file(path: str) -> AcsCharacter:
    """Parsea y decodifica un archivo .acs completo: todas las imágenes y
    todas las animaciones, ya como imágenes PIL RGBA listas para empaquetar
    en un sprite sheet con el mismo esquema que usa app/animation.py."""
    with open(path, "rb") as f:
        data = f.read()

    (magic,) = struct.unpack_from("<I", data, 0)
    if magic != MAGIC:
        raise AcsParseError(f"firma inválida {magic:#x} (se esperaba {MAGIC:#x}) — ¿es un .acs real?")

    offset = 4
    char_off, _char_size, offset = _read_locator(data, offset)
    anim_off, _anim_size, offset = _read_locator(data, offset)
    img_off, _img_size, offset = _read_locator(data, offset)
    _aud_off, _aud_size, offset = _read_locator(data, offset)

    # --- bloque de personaje: versión, GUID, tamaño de canvas, índice transparente ---
    pos = char_off
    pos += 4  # minorVersion, majorVersion (no los necesitamos)
    pos += 8  # offset/tamaño de la sub-tabla "Names" (no la necesitamos)
    pos += 16  # GUID del personaje
    canvas_w, canvas_h = struct.unpack_from("<HH", data, pos)
    pos += 4
    (transparent_index,) = struct.unpack_from("<B", data, pos)
    pos += 1
    pos += 4  # styleFlags
    pos += 4  # DWORD constante sin documentar (0x2 en los 3 archivos probados)

    palette = _find_palette(data, pos)

    # --- lista de imágenes: se decodifican TODAS de una (se reusan muchísimo) ---
    pos = img_off
    (image_count,) = struct.unpack_from("<I", data, pos)
    pos += 4
    image_records = []
    for _ in range(image_count):
        loc_off, _loc_size = struct.unpack_from("<II", data, pos)
        pos += 8
        pos += 4  # checksum: algoritmo nunca documentado, no hace falta
        image_records.append(loc_off)

    decoded_rgba: list = [None] * image_count
    for i, rec_off in enumerate(image_records):
        p = rec_off
        p += 1  # byte de flag sin interpretar (siempre 0 en los archivos probados)
        width, height = struct.unpack_from("<HH", data, p)
        p += 4
        (compressed,) = struct.unpack_from("<B", data, p)
        p += 1
        (byte_count,) = struct.unpack_from("<I", data, p)
        p += 4
        pixel_bytes = data[p : p + byte_count]
        indexed = _decode_indexed_image(pixel_bytes, bool(compressed), width, height)
        decoded_rgba[i] = _indexed_to_rgba(indexed, width, height, palette, transparent_index)

    # --- lista de animaciones ---
    pos = anim_off
    (anim_count,) = struct.unpack_from("<I", data, pos)
    pos += 4
    anim_headers = []
    for _ in range(anim_count):
        name, pos = _read_string(data, pos)
        ext_off, _ext_size, pos = _read_locator(data, pos)
        anim_headers.append((name, ext_off))

    character = AcsCharacter(canvas_w, canvas_h)
    character.images = decoded_rgba
    for name, ext_off in anim_headers:
        p = ext_off
        _upper_name, p = _read_string(data, p)
        p += 1  # transitionType
        _return_name, p = _read_string(data, p)
        (frame_count,) = struct.unpack_from("<H", data, p)
        p += 2

        animation = AcsAnimation(name=name)
        for _ in range(frame_count):
            (image_count_in_frame,) = struct.unpack_from("<H", data, p)
            p += 2
            images = []
            for _ in range(image_count_in_frame):
                img_idx, x, y = struct.unpack_from("<Ihh", data, p)
                p += 8
                images.append((img_idx, x, y))
            _audio_idx, duration_hundredths, _exit_frame = struct.unpack_from("<Hhh", data, p)
            p += 6
            (branch_count,) = struct.unpack_from("<B", data, p)
            p += 1 + branch_count * 4
            (overlay_count,) = struct.unpack_from("<B", data, p)
            p += 1
            for _ in range(overlay_count):
                p += 2  # mouth, replaceTop
                _img2, _unk, has_region = struct.unpack_from("<HBB", data, p)
                p += 4
                p += 8  # x,y,w,h del overlay
                if has_region:
                    (region_size,) = struct.unpack_from("<I", data, p)
                    p += 4 + region_size

            animation.frames.append(
                AcsFrame(images=images, duration_ms=max(duration_hundredths, 1) * 10)
            )
        character.animations.append(animation)

    return character


def _try_palette_at(data: bytes, offset: int):
    if offset + 4 > len(data):
        return None
    (count,) = struct.unpack_from("<I", data, offset)
    if not (1 <= count <= 256):
        return None
    entries_off = offset + 4
    end = entries_off + count * 4
    if end > len(data):
        return None
    chunk = data[entries_off:end]
    # Cada entrada de paleta es un COLORREF de 4 bytes (B,G,R,0) — el 4to
    # byte casi siempre es 0, así que lo usamos como heurística para
    # confirmar "esto es realmente una paleta y no datos random".
    zero_fourth = sum(1 for i in range(3, len(chunk), 4) if chunk[i] == 0)
    if zero_fourth / count <= 0.9:
        return None
    palette = [(chunk[i + 2], chunk[i + 1], chunk[i]) for i in range(0, len(chunk), 4)]
    return palette


def _find_palette(data: bytes, start_offset: int, max_scan: int = 4000):
    """La paleta viene justo después del bloque de personaje — salvo que
    haya un bloque opcional de "globo de texto" (BALLOONINFO) en el medio,
    en cuyo caso hay que saltarlo primero. No conocemos el bit exacto de
    styleFlags que indica su presencia con certeza, así que lo detectamos
    de forma empírica: buscamos algo que parezca el STRING con el nombre de
    la tipografía (ej. "MS Sans Serif") y calculamos la paleta a partir de
    ahí. Si no aparece, probamos directo en start_offset."""
    direct = _try_palette_at(data, start_offset)
    if direct:
        return direct

    for candidate in range(start_offset, min(start_offset + max_scan, len(data) - 4)):
        (count,) = struct.unpack_from("<I", data, candidate)
        if not (1 <= count <= 64):
            continue
        str_start = candidate + 4
        n_bytes = count * 2
        if str_start + n_bytes + 2 > len(data):
            continue
        raw = data[str_start : str_start + n_bytes]
        try:
            text = raw.decode("utf-16-le")
        except UnicodeDecodeError:
            continue
        if not all(32 <= ord(ch) < 127 for ch in text):
            continue
        if data[str_start + n_bytes : str_start + n_bytes + 2] != b"\x00\x00":
            continue
        after_string = str_start + n_bytes + 2
        # Lo que sigue al nombre de tipografía dentro de BALLOONINFO:
        # fontHeight (LONG) + fontWeight (ULONG) + italic (BYTE) + unknown (BYTE).
        # Lo que precede al nombre (numTextLines, charsPerLine, 3x RGBQUAD) no
        # importa acá porque el string se ubica escaneando, no por offset fijo.
        palette_offset = after_string + 4 + 4 + 1 + 1
        palette = _try_palette_at(data, palette_offset)
        if palette:
            return palette

    raise AcsParseError("no se encontró la paleta de colores del personaje")


def _compose_frame(character: AcsCharacter, layers: tuple) -> "PIL.Image.Image":
    """Compone las 1+ imágenes de un frame en un único RGBA del tamaño del
    canvas del personaje. El spec de MS Agent dice que se dibujan en orden
    INVERSO (la última imagen de la lista va primero, abajo de todo) — en la
    práctica, la enorme mayoría de los frames de estos personajes tiene una
    sola imagen y esto es un simple passthrough."""
    from PIL import Image

    if len(layers) == 1:
        img_idx, x, y = layers[0]
        base = character.images[img_idx]
        if (x, y) == (0, 0) and base.size == (character.canvas_width, character.canvas_height):
            return base

    canvas = Image.new("RGBA", (character.canvas_width, character.canvas_height), (0, 0, 0, 0))
    for img_idx, x, y in reversed(layers):
        canvas.alpha_composite(character.images[img_idx], (x, y))
    return canvas


def build_agent_assets(
    character: AcsCharacter, name: str, dest_dir: Path, atlas_columns: int = 20
) -> dict:
    """Genera `agent.json` + `map.png` en `dest_dir` a partir de un
    `AcsCharacter` ya decodificado, en el mismo esquema que usa el resto del
    roster (ver app/animation.py) — así el motor de animación no necesita
    saber que estos personajes vinieron de un `.acs` en vez de clippy.js.

    La usan tanto tools/fetch_acs_assets.py (para los 3 personajes con fuente
    conocida) como tools/acs_importer.py (para un `.acs` que el propio
    usuario le pase a mano). Devuelve estadísticas básicas para loguear.
    """
    from PIL import Image

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Muchísimos frames repiten exactamente la misma imagen (ej. una pose de
    # "reposo" usada por varias animaciones) — se compone cada combinación
    # única de imágenes UNA sola vez y se le asigna una celda compartida en
    # el sprite sheet, en vez de una celda por frame.
    cell_by_layer_signature: dict[tuple, int] = {}
    atlas_cells: list = []
    animations_json: dict[str, list[dict]] = {}

    for animation in character.animations:
        frames_json = []
        for frame in animation.frames:
            signature = tuple(frame.images)
            cell_index = cell_by_layer_signature.get(signature)
            if cell_index is None:
                cell_index = len(atlas_cells)
                cell_by_layer_signature[signature] = cell_index
                atlas_cells.append(_compose_frame(character, signature))
            col, row = cell_index % atlas_columns, cell_index // atlas_columns
            x, y = col * character.canvas_width, row * character.canvas_height
            frames_json.append({"duration": frame.duration_ms, "images": [[x, y]]})
        animations_json[animation.name] = frames_json

    rows = (len(atlas_cells) + atlas_columns - 1) // atlas_columns
    sheet = Image.new(
        "RGBA",
        (atlas_columns * character.canvas_width, max(rows, 1) * character.canvas_height),
        (0, 0, 0, 0),
    )
    for i, cell in enumerate(atlas_cells):
        col, row = i % atlas_columns, i // atlas_columns
        sheet.alpha_composite(cell, (col * character.canvas_width, row * character.canvas_height))

    sheet.save(dest_dir / "map.png")
    agent = {
        "name": name,
        "sprite": "map.png",
        "frame_width": character.canvas_width,
        "frame_height": character.canvas_height,
        "animations": animations_json,
    }
    (dest_dir / "agent.json").write_text(
        json.dumps(agent, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "animation_count": len(animations_json),
        "frame_count": sum(len(f) for f in animations_json.values()),
        "unique_images": len(atlas_cells),
    }
