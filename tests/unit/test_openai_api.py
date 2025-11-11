from unittest.mock import MagicMock, patch

from rich.console import Console

from gen_captions import openai_generic_client
from gen_captions.config import Config


@patch("openai.OpenAI")
def test_openai_generic_client(mock_openai):
    config = Config()
    console = Console(record=True)
    logger = MagicMock()

    config._llm_api_key = "test-key"
    config._llm_base_url = "https://api.openai.com/v1"
    config._llm_model = "gpt-3.5-turbo"
    config._current_backend = "openai"
    with patch(
        "gen_captions.openai_generic_client.encode_image",
        return_value="encoded-image",
    ):
        client = openai_generic_client.OpenAIGenericClient(
            config, console, logger
        )

        # mock response
        mock_instance = mock_openai.return_value
        mock_instance.chat.completions.create.return_value = (
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="[trigger] some desc"
                        )
                    )
                ]
            )
        )

        desc = client.generate_description("fake_path.jpg")
        assert "[trigger]" in desc
        mock_instance.chat.completions.create.assert_called_once()
