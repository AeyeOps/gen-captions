"""Module for testing default configuration settings."""

from pathlib import Path

import tomllib

from gen_captions.config import Config


def _set_temp_config(monkeypatch, tmp_path):
    config_file = tmp_path / "local.yaml"
    config_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("GEN_CAPTIONS_CONFIG", str(config_file))
    return config_file


def test_config_defaults(monkeypatch, tmp_path):
    """Test that config uses default env if no environment variables are
    set."""
    # Unset any relevant environment variables
    monkeypatch.delenv("GETCAP_THREAD_POOL", raising=False)
    monkeypatch.delenv("GETCAP_THROTTLE_RETRIES", raising=False)
    _set_temp_config(monkeypatch, tmp_path)

    config = Config()
    assert config.THREAD_POOL == 10
    assert config.THROTTLE_RETRIES == 10
    assert config.LOG_LEVEL == "INFO"


def test_config_backend(monkeypatch, tmp_path):
    """Test set_backend method picks up env variables for openai or grok."""
    _set_temp_config(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    c = Config()
    c.set_backend("openai")
    assert c.LLM_API_KEY == "test-key"
    assert c.LLM_MODEL == "gpt-5-mini"
    assert c.LLM_BASE_URL == "https://api.openai.com/v1"


def test_removal_threshold_defaults(monkeypatch, tmp_path):
    _set_temp_config(monkeypatch, tmp_path)
    config = Config()
    thresholds = config.get_removal_thresholds()

    assert thresholds["is_solo_p"] == 0.9
    assert thresholds["is_woman_p"] == 0.9
    assert thresholds["is_man_p"] == 0.9


def test_version_matches_pyproject(monkeypatch, tmp_path):
    _set_temp_config(monkeypatch, tmp_path)
    config = Config()

    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        pyproject_data = tomllib.load(handle)

    expected_version = pyproject_data["project"]["version"]
    assert config.VERSION == expected_version
