import json

from app.i18n import SUPPORTED_LANGS, Translator
from app.resources import resource_path


def _load_raw(lang):
    with open(resource_path("locales", f"{lang}.json"), encoding="utf-8") as f:
        return json.load(f)


def test_all_locales_have_the_same_keys():
    key_sets = {lang: set(_load_raw(lang).keys()) for lang in SUPPORTED_LANGS}
    base_lang, base_keys = next(iter(key_sets.items()))
    for lang, keys in key_sets.items():
        assert keys == base_keys, (
            f"locales/{lang}.json y locales/{base_lang}.json tienen claves distintas: "
            f"{keys.symmetric_difference(base_keys)}"
        )


def test_translator_falls_back_to_key_when_missing():
    translator = Translator("es")
    assert translator.t("clave.que.no.existe") == "clave.que.no.existe"


def test_translator_formats_placeholders():
    translator = Translator("en")
    text = translator.t("tray.tooltip", character="Clippy")
    assert "Clippy" in text


def test_tips_list_is_not_empty_in_every_language():
    for lang in SUPPORTED_LANGS:
        translator = Translator(lang)
        assert len(translator.list("tips")) > 0
