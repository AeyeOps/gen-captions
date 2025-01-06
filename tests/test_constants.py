# tests/test_constants.py

from gen_captions.config import Config

config = Config()
config.set_backend("openai")


def test_constants():
    assert isinstance(config.THREAD_POOL, int)
    assert isinstance(config.THROTTLE_RETRIES, int)
    assert isinstance(config.THROTTLE_BACKOFF_FACTOR, float)
    assert isinstance(config.THROTTLE_SUBMISSION_RATE, float)
    assert isinstance(config.LOG_LEVEL, str)
