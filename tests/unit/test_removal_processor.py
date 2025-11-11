from unittest.mock import MagicMock, patch

from rich.console import Console

from gen_captions.config import Config
from gen_captions.removal_processor import (
    remove_mismatched_images,
)


def _build_config(monkeypatch, tmp_path):
    config_path = tmp_path / "local.yaml"
    config_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("GEN_CAPTIONS_CONFIG", str(config_path))
    return Config()


@patch("gen_captions.removal_processor.get_llm_client")
def test_remove_mismatched_images_moves_files(
    mock_get_llm_client, tmp_path, monkeypatch
):
    mock_client = MagicMock()
    mock_client.generate_removal_metadata.return_value = {
        "thought": "Group of men",
        "is_solo_p": 0.2,
        "is_woman_p": 0.1,
        "is_man_p": 0.95,
    }
    mock_get_llm_client.return_value = mock_client

    logger = MagicMock()
    console = Console(record=True)
    config = _build_config(monkeypatch, tmp_path)

    image_path = tmp_path / "keep.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0")
    caption_path = tmp_path / "keep.txt"
    caption_path.write_text("caption", encoding="utf-8")

    summary = remove_mismatched_images(
        image_directory=str(tmp_path),
        backend="openai",
        config=config,
        console=console,
        logger=logger,
        desired_gender="women",
        require_solo=None,
    )

    assert summary["removed"] == 1
    removed_file = tmp_path / "removed" / "keep.jpg"
    removed_caption = tmp_path / "removed" / "keep.txt"
    assert removed_file.exists()
    assert removed_caption.exists()
    assert not image_path.exists()


@patch("gen_captions.removal_processor.get_llm_client")
def test_remove_mismatched_images_keeps_matches(
    mock_get_llm_client, tmp_path, monkeypatch
):
    mock_client = MagicMock()
    mock_client.generate_removal_metadata.return_value = {
        "thought": "Solo woman",
        "is_solo_p": 0.95,
        "is_woman_p": 0.96,
        "is_man_p": 0.1,
    }
    mock_get_llm_client.return_value = mock_client

    logger = MagicMock()
    console = Console(record=True)
    config = _build_config(monkeypatch, tmp_path)

    image_path = tmp_path / "match.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0")

    summary = remove_mismatched_images(
        image_directory=str(tmp_path),
        backend="openai",
        config=config,
        console=console,
        logger=logger,
        desired_gender="women",
        require_solo=None,
    )

    assert summary["removed"] == 0
    assert image_path.exists()
    removed_file = tmp_path / "removed" / "match.jpg"
    assert not removed_file.exists()


@patch("gen_captions.removal_processor.get_llm_client")
def test_remove_by_solo_flag(
    mock_get_llm_client, tmp_path, monkeypatch
):
    mock_client = MagicMock()
    mock_client.generate_removal_metadata.return_value = {
        "thought": "Crowd shot",
        "is_solo_p": 0.2,
        "is_woman_p": 0.4,
        "is_man_p": 0.4,
    }
    mock_get_llm_client.return_value = mock_client

    logger = MagicMock()
    console = Console(record=True)
    config = _build_config(monkeypatch, tmp_path)

    image_path = tmp_path / "solo.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0")

    summary = remove_mismatched_images(
        image_directory=str(tmp_path),
        backend="openai",
        config=config,
        console=console,
        logger=logger,
        desired_gender=None,
        require_solo=True,
    )

    assert summary["removed"] == 1
    assert not image_path.exists()
