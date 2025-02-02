from unittest.mock import MagicMock, patch

from rich.console import Console

from gen_captions.config import Config
from gen_captions.openai_generic_client import OpenAIGenericClient


@patch("openai.OpenAI")
def test_openai_generic_client(mock_openai):
    config = Config()
    console = Console(record=True)
    logger = MagicMock()

    # Set a sample model that's not in MODEL_CONFIG so it uses default
    config._config["LLM_MODEL"] = "gpt-3.5-turbo"
    client = OpenAIGenericClient(config, console, logger)

    # mock response
    mock_instance = mock_openai.return_value
    mock_instance.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(message=MagicMock(content="[trigger] some desc"))
        ]
    )

    desc = client.generate_description("fake_path.jpg")
    assert "[trigger]" in desc
    mock_instance.chat.completions.create.assert_called_once()
