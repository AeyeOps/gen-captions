"""A module that contains utility functions for the gen_captions package.

This module contains utility functions that are used by the
gen_captions.
"""

import base64
import os


def prompt_exists(text_file):
    """Check if the prompt file already exists and is not empty."""
    return os.path.exists(text_file) and os.stat(text_file).st_size > 0


def encode_image(image_path):
    """Encode the image to base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
