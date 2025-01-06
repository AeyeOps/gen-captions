import os
from unittest.mock import patch
import pytest
from gen_captions import config

@patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "OPENAI_MODEL": "fake-model"})
def test_set_backend_openai():
    config.set_backend("openai")
    assert config.LLM_API_KEY == "fake-key"
    assert config.LLM_MODEL == "fake-model"
