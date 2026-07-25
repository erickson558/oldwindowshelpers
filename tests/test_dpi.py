from app.dpi import make_process_dpi_aware


def test_make_process_dpi_aware_does_not_raise():
    # No hay forma de verificar el estado de DPI awareness de forma
    # confiable en un test (y no se puede llamar dos veces con distinto modo
    # en el mismo proceso), pero sí podemos asegurar que nunca tira una
    # excepción sin manejar, sea cual sea el Windows donde corra.
    make_process_dpi_aware()
