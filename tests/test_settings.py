from app import settings


def test_load_returns_defaults_when_no_config_file(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config = settings.load()
    assert config == settings.DEFAULTS


def test_save_then_load_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config = settings.load()
    config["character"] = "Merlin"
    config["always_on_top"] = False
    settings.save(config)

    reloaded = settings.load()
    assert reloaded["character"] == "Merlin"
    assert reloaded["always_on_top"] is False
