"""app/balloon.py tuvo un bug real (encontrado por revisión adversarial antes
de publicarse, nunca llegó a los usuarios): el wrap de texto solo cortaba en
espacios, así que una sola palabra sin espacios más ancha que WRAP_WIDTH (una
URL, un typo de traducción que se comió un espacio) generaba un globo de
diálogo de miles de píxeles de ancho en vez de respetar el tamaño esperado.
Esta prueba fija ese comportamiento para que no vuelva a colarse."""

from app.balloon import WRAP_WIDTH, render_balloon


def test_short_text_produces_a_reasonably_sized_balloon():
    image, _tail_x, _tail_y = render_balloon("Recorda guardar tu trabajo seguido.")
    assert image.width < WRAP_WIDTH * 2
    assert image.height < 150


def test_long_unbroken_word_does_not_produce_an_unbounded_balloon():
    # Antes del fix, esto generaba un globo de ~2700px de ancho: una sola
    # "palabra" (sin espacios) simplemente no se cortaba nunca.
    image, _tail_x, _tail_y = render_balloon("A" * 300)
    assert image.width < WRAP_WIDTH * 2


def test_render_balloon_is_stable_for_empty_text():
    image, _tail_x, _tail_y = render_balloon("")
    assert image.width > 0 and image.height > 0
