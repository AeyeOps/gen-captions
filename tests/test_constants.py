# tests/test_constants.py

from gen_captions import constants

def test_constants():
    assert isinstance(constants.THREAD_POOL, int)
    assert isinstance(constants.THROTTLE_RETRIES, int)
    assert isinstance(constants.THROTTLE_BACKOFF_FACTOR, float)
    assert isinstance(constants.THROTTLE_SUBMISSION_RATE, float)
    assert isinstance(constants.LOG_LEVEL, str)
