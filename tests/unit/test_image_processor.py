import os
import tempfile
from unittest.mock import MagicMock, patch

from rich.console import Console

from gen_captions.config import Config
from gen_captions.image_processor import process_images


def fake_llm_generate_description(image_path):
    # Return a description with [trigger], as if the LLM responded
    return "[trigger], a test description"


@patch("gen_captions.image_processor.get_llm_client")
def test_process_images(mock_get_llm_client):
    mock_client = MagicMock()
    mock_client.generate_description.side_effect = (
        fake_llm_generate_description
    )
    mock_get_llm_client.return_value = mock_client

    logger = MagicMock()
    console = Console(record=True)

    with (
        tempfile.TemporaryDirectory() as img_dir,
        tempfile.TemporaryDirectory() as cap_dir,
    ):
        # Create a fake image
        img_path = os.path.join(img_dir, "test.jpg")
        with open(img_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0")  # minimal JPEG header

        config = Config()
        process_images(
            image_directory=img_dir,
            caption_directory=cap_dir,
            backend="openai",
            config=config,
            console=console,
            logger=logger,
        )

        # Check that the .txt file was written with the [trigger] description
        out_file = os.path.join(cap_dir, "test.txt")
        with open(out_file, encoding="utf-8") as f:
            text = f.read()
            assert "[trigger]" in text

        # Ensure the LLM was called
        mock_client.generate_description.assert_called_once()
