"""Renderiza el globo de diálogo estilo "balloon" clásico de Windows XP
(el de los tooltips / Office Assistant) como un único bitmap RGBA con Pillow.

Por qué un solo bitmap "horneado" (baked) en vez de Canvas + Label superpuestos:
la transparencia de este proyecto usa color-key (`-transparentcolor`, ver
app/character_window.py), que NO hace alpha blending real — cualquier píxel
semitransparente se mezcla con el color llave ANTES de que Windows lo recorte.
Si compusiéramos la forma redondeada + la cola + el texto con varios widgets
Tkinter superpuestos sobre el color llave, cada borde antialiased que produce
`ImageDraw` (el contorno del rounded-rect, los lados de la cola, el propio
texto) dejaría el mismo halo mágenta que ya afectó a los sprites de los
personajes (ver `_harden_alpha` en app/animation.py — el mismo bug de fondo,
ya golpeado dos veces en este repo). Al dibujar TODO —sombra, cuerpo, cola y
texto— en una sola imagen RGBA y "endurecer" el alfa al final con el mismo
criterio que el motor de animación, garantizamos que cada píxel quede 100%
opaco o 100% invisible: cero posibilidad de fringing.
"""

from __future__ import annotations

from PIL import Image, ImageColor, ImageDraw, ImageFont

# Mismo umbral y misma razón que ALPHA_HARDEN_THRESHOLD en app/animation.py:
# binarizar el alfa evita que los bordes antialiased de las formas (rounded
# rect, cola, texto) se fundan con el color llave de la ventana antes de
# recortarse.
ALPHA_HARDEN_THRESHOLD = 140

BORDER_COLOR = (64, 64, 64, 255)  # gris casi negro: borde fino clásico de tooltip XP
# La "sombra" no puede ser semitransparente de verdad (no hay blending real
# posible con color-key), así que se hornea como una silueta sólida y opaca
# de un tono oscurecido, apenas desplazada — el ojo la lee como sombra suave
# aunque en el bitmap sea 100% opaca.
SHADOW_COLOR = (120, 120, 120, 255)
TEXT_COLOR = (0, 0, 0, 255)

PADDING_X = 10
PADDING_Y = 8
CORNER_RADIUS = 10
BORDER_WIDTH = 2
SHADOW_OFFSET = 4
TAIL_WIDTH = 18  # ancho de la base de la cola triangular
TAIL_HEIGHT = 14  # cuánto sobresale la cola por debajo del cuerpo
TAIL_MARGIN_RIGHT = 24  # separación entre el borde derecho del cuerpo y la cola
WRAP_WIDTH = 220  # mismo ancho de wrap que tenía el Label plano anterior
MIN_BODY_WIDTH = 90  # deja lugar de sobra para que la cola no se salga del cuerpo
LINE_SPACING = 4
FONT_SIZE = 12  # ~9pt de Tk a 96dpi, para parecerse al tamaño previo

# "Comic Sans MS" (nombre de familia, no de archivo) NO sirve acá: Pillow
# busca un ARCHIVO por ese nombre, no consulta el registro de fuentes de
# Windows por nombre de familia, así que ese string nunca resuelve y sería
# código muerto. "comicbd.ttf" (la variante negrita) sí es un archivo real,
# de reemplazo razonable si por algún motivo faltara la regular.
_FONT_CANDIDATES = ("comic.ttf", "comicbd.ttf", "arial.ttf")


def _load_font() -> ImageFont.FreeTypeFont:
    """Busca Comic Sans (el "toque" clásico del Ayudante) y cae a Arial o al
    font por defecto de Pillow si el sistema no la tiene instalada."""
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


def _hard_break(draw: ImageDraw.ImageDraw, word: str, font, max_width: int) -> list[str]:
    """Parte `word` letra por letra hasta que cada pedazo entre en max_width.

    Sin esto, una palabra sin espacios más ancha que max_width (una URL, un
    typo de traducción que se comió un espacio, una palabra compuesta larga)
    nunca se corta y el globo entero termina tan ancho como el texto —
    reproducido y confirmado con un string de 300 caracteres, que sin este
    corte generaba un globo de más de 2700px de ancho. El Label de Tkinter
    que este módulo reemplaza SÍ cortaba a media palabra en ese caso
    (`wraplength` de Tk corta donde haga falta), así que esto replica ese
    comportamiento en vez de dejarlo regresar.
    """
    pieces: list[str] = []
    remaining = word
    while draw.textbbox((0, 0), remaining, font=font)[2] > max_width and len(remaining) > 1:
        lo, hi, fit = 1, len(remaining), 1
        while lo <= hi:
            mid = (lo + hi) // 2
            width = draw.textbbox((0, 0), remaining[:mid], font=font)[2]
            if width <= max_width:
                fit = mid
                lo = mid + 1
            else:
                hi = mid - 1
        fit = max(1, fit)  # siempre progresar, incluso si max_width es menor que un carácter
        pieces.append(remaining[:fit])
        remaining = remaining[fit:]
    pieces.append(remaining)
    return pieces


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    """Envuelve `text` a mano (Pillow no hace wrap automático) respetando los
    saltos de línea explícitos que ya traiga, palabra por palabra, igual que
    hacía `wraplength` en el Label de Tkinter que reemplaza este módulo."""
    wrapped_lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        if not words or words == [""]:
            wrapped_lines.append("")
            continue
        current = ""
        for word in words:
            for chunk in _hard_break(draw, word, font, max_width):
                candidate = f"{current} {chunk}" if current else chunk
                width = draw.textbbox((0, 0), candidate, font=font)[2]
                if width <= max_width or not current:
                    current = candidate
                else:
                    wrapped_lines.append(current)
                    current = chunk
        wrapped_lines.append(current)
    return "\n".join(wrapped_lines)


def render_balloon(text: str, bg_color: str = "#ffffe1") -> tuple[Image.Image, int, int]:
    """Renderiza el globo completo (sombra + cuerpo redondeado + cola + texto)
    como una imagen RGBA con el alfa ya endurecido, lista para mostrarse en una
    ventana Toplevel color-key.

    Devuelve `(imagen, tail_tip_x, tail_tip_y)`: las coordenadas de la punta de
    la cola dentro de la imagen, por si en el futuro se quiere alinear esa
    punta exactamente contra el personaje (hoy `character_window.py` sigue
    posicionando el globo con el mismo cálculo relativo que usaba antes).
    """
    bg_rgba = ImageColor.getrgb(bg_color) + (255,)
    font = _load_font()

    # Medimos el texto envuelto con un draw "de prueba" sobre una imagen de
    # 1x1: Pillow permite medir texto sin necesidad de conocer aún el tamaño
    # final del lienzo.
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wrapped = _wrap_text(probe, text, font, WRAP_WIDTH)
    text_bbox = probe.multiline_textbbox((0, 0), wrapped, font=font, spacing=LINE_SPACING)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    body_w = max(text_w + 2 * PADDING_X, MIN_BODY_WIDTH)
    body_h = text_h + 2 * PADDING_Y

    canvas_w = body_w + SHADOW_OFFSET
    canvas_h = body_h + SHADOW_OFFSET + TAIL_HEIGHT

    image = Image.new("RGBA", (round(canvas_w), round(canvas_h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Geometría de la cola: apunta hacia abajo-a-la-derecha (el globo se
    # posiciona arriba-a-la-izquierda del personaje, así que la cola "mira"
    # hacia donde está la cabeza del personaje).
    tail_base_right = body_w - TAIL_MARGIN_RIGHT
    tail_base_left = tail_base_right - TAIL_WIDTH
    tail_apex_x = tail_base_right + TAIL_WIDTH * 0.6
    tail_apex_y_body = body_h + TAIL_HEIGHT

    def tail_points(offset_x: float, offset_y: float) -> list[tuple[float, float]]:
        return [
            (tail_base_left + offset_x, body_h - 1 + offset_y),
            (tail_base_right + offset_x, body_h - 1 + offset_y),
            (tail_apex_x + offset_x, tail_apex_y_body + offset_y),
        ]

    # 1) Sombra: silueta del cuerpo + cola, desplazada, opaca y de un tono
    #    oscurecido — ver comentario junto a SHADOW_COLOR sobre por qué no es
    #    semitransparente de verdad. Sin outline, así que no tiene el problema
    #    de costura que sí tiene el cuerpo (ver más abajo): dos rellenos del
    #    mismo color que se tocan no dejan ninguna línea visible entre sí.
    draw.rounded_rectangle(
        (SHADOW_OFFSET, SHADOW_OFFSET, SHADOW_OFFSET + body_w, SHADOW_OFFSET + body_h),
        radius=CORNER_RADIUS,
        fill=SHADOW_COLOR,
    )
    draw.polygon(tail_points(SHADOW_OFFSET, SHADOW_OFFSET), fill=SHADOW_COLOR)

    # 2) Cuerpo: rounded-rect amarillo pálido con borde fino oscuro.
    draw.rounded_rectangle(
        (0, 0, body_w, body_h),
        radius=CORNER_RADIUS,
        fill=bg_rgba,
        outline=BORDER_COLOR,
        width=BORDER_WIDTH,
    )

    # 3) "Borrar" el tramo del borde inferior del cuerpo justo donde nace la
    #    cola: pintamos ese tramo con el mismo color de relleno, tapando la
    #    línea de contorno ahí. Sin este paso, el contorno del rounded-rect
    #    cruza recto por debajo de la cola y la cola (con su propio contorno)
    #    se dibuja encima como un triángulo pegado aparte — se ve una costura
    #    horizontal justo donde debería fluir un solo contorno continuo.
    draw.rectangle(
        (tail_base_left - 1, body_h - BORDER_WIDTH, tail_base_right + 1, body_h + BORDER_WIDTH),
        fill=bg_rgba,
    )

    # 4) Cola: relleno sin contorno propio (el "hueco" de arriba ya lo conecta
    #    sin costura con el cuerpo), más solo los DOS lados inclinados
    #    dibujados como líneas — la base de la cola queda sin línea, así el
    #    contorno del cuerpo (interrumpido en el paso 3) se continúa
    #    naturalmente por los lados de la cola en vez de cruzarse con ellos.
    draw.polygon(tail_points(0, 0), fill=bg_rgba)
    draw.line(
        [(tail_base_left, body_h), (tail_apex_x, tail_apex_y_body)],
        fill=BORDER_COLOR,
        width=BORDER_WIDTH,
    )
    draw.line(
        [(tail_base_right, body_h), (tail_apex_x, tail_apex_y_body)],
        fill=BORDER_COLOR,
        width=BORDER_WIDTH,
    )

    # 5) Texto, centrado en el área de contenido (dentro del padding).
    text_x = PADDING_X - text_bbox[0]
    text_y = PADDING_Y - text_bbox[1]
    draw.multiline_text(
        (text_x, text_y), wrapped, font=font, fill=TEXT_COLOR, spacing=LINE_SPACING
    )

    image = _harden_alpha(image)
    return image, round(tail_apex_x), round(tail_apex_y_body)


def _harden_alpha(image: Image.Image, threshold: int = ALPHA_HARDEN_THRESHOLD) -> Image.Image:
    """Binariza el canal alfa (ver docstring del módulo): evita el halo de
    color-key en los bordes antialiased de la forma y del texto."""
    r, g, b, a = image.split()
    a = a.point(lambda p: 255 if p >= threshold else 0)
    return Image.merge("RGBA", (r, g, b, a))
