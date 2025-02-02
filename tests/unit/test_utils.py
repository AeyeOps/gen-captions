import tempfile

from gen_captions.utils import encode_image, prompt_exists


def test_prompt_exists():
    with tempfile.NamedTemporaryFile() as tmpfile:
        # Empty file => prompt_exists should be False
        assert not prompt_exists(tmpfile.name)
        # Write something
        tmpfile.write(b"hello")
        tmpfile.flush()
        assert prompt_exists(tmpfile.name)


def test_encode_image():
    with tempfile.NamedTemporaryFile(suffix=".jpg") as tmpfile:
        tmpfile.write(b"\xFF\xD8\xFF\xE0")  # Minimal JPEG header bytes
        tmpfile.flush()
        encoded = encode_image(tmpfile.name)
        # Basic check: should be base64 string, not empty
        assert len(encoded) > 0
        assert isinstance(encoded, str)
