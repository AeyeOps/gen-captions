"""Tests for ConfigManager default config handling."""

from rich.console import Console

from gen_captions.config_manager import ConfigManager


def test_load_default_config_creates_missing_file(monkeypatch, tmp_path):
    manager = ConfigManager(Console(record=True))

    target_path = tmp_path / "default.yaml"

    monkeypatch.setattr(
        ConfigManager,
        "get_default_config_path",
        lambda self: target_path,
        raising=False,
    )

    data = manager.load_default_config()

    assert target_path.exists(), "default.yaml should be copied to the user config dir"
    assert isinstance(data, dict)
    assert data.get("config_version") == "1.0"
