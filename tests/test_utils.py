# tests/test_utils.py

import os
import tempfile

from gen_captions.utils import encode_image, prompt_exists


def test_prompt_exists():
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"Test content")
        tmp_filename = tmp_file.name
    assert prompt_exists(tmp_filename) == True
    os.remove(tmp_filename)
    assert prompt_exists(tmp_filename) == False


def test_encode_image():
    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False
    ) as tmp_file:
        tmp_file.write(b"Test image content")
        image_filename = tmp_file.name
    encoded = encode_image(image_filename)
    assert isinstance(encoded, str)
    os.remove(image_filename)
