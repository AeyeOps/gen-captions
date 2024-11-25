# tests/test_image_processor.py

import os
import tempfile
from gen_captions.image_processor import process_images

def test_process_images_empty_dir():
    with tempfile.TemporaryDirectory() as image_dir, tempfile.TemporaryDirectory() as caption_dir:
        process_images(image_dir, caption_dir)
        # Check that caption directory is still empty
        assert len(os.listdir(caption_dir)) == 0
