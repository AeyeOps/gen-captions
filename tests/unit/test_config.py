"""Module for testing default configuration settings."""

from gen_captions.config import Config


def test_config_defaults(monkeypatch):
    """Test that config uses default env if no environment variables are
    set."""
    # Unset any relevant environment variables
    monkeypatch.delenv("GETCAP_THREAD_POOL", raising=False)
    monkeypatch.delenv("GETCAP_THROTTLE_RETRIES", raising=False)

    config = Config()
    assert config.THREAD_POOL == 10
    assert config.THROTTLE_RETRIES == 10
    assert config.LOG_LEVEL == "INFO"


def test_config_backend(monkeypatch):
    """Test set_backend method picks up env variables for openai or grok."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv(
        "OPENAI_BASE_URL", "https://api.openai.fake"
    )
    c = Config()
    c.set_backend("openai")
    assert c.LLM_API_KEY == "test-key"
    assert c.LLM_MODEL == "test-model"
    assert c.LLM_BASE_URL == "https://api.openai.fake"
