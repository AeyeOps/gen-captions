"""Unit tests for local server detection."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from rich.console import Console

from gen_captions.config import Config
from gen_captions.openai_generic_client import (
    OpenAIGenericClient,
)


class TestLocalServerDetection:
    """Test suite for local server availability detection."""

    @patch("socket.socket")
    @patch("openai.OpenAI")
    def test_lmstudio_server_not_running(
        self, mock_openai, mock_socket
    ):
        """Test LM Studio server down detection."""
        config = Config()
        config.set_backend("lmstudio")
        console = Console()
        logger = MagicMock()

        # Mock socket connection failure
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = (
            1  # Connection refused
        )
        mock_socket.return_value = mock_sock_instance

        with pytest.raises(ConnectionError) as exc_info:
            OpenAIGenericClient(config, console, logger)

        assert "lmstudio" in str(exc_info.value).lower()
        assert "1234" in str(exc_info.value)

    @patch("socket.socket")
    @patch("openai.OpenAI")
    def test_ollama_server_not_running(
        self, mock_openai, mock_socket
    ):
        """Test Ollama server down detection."""
        config = Config()
        config.set_backend("ollama")
        console = Console()
        logger = MagicMock()

        # Mock socket connection failure
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 1
        mock_socket.return_value = mock_sock_instance

        with pytest.raises(ConnectionError) as exc_info:
            OpenAIGenericClient(config, console, logger)

        assert "ollama" in str(exc_info.value).lower()
        assert "11434" in str(exc_info.value)

    @patch("socket.socket")
    @patch("openai.OpenAI")
    def test_lmstudio_server_running(
        self, mock_openai, mock_socket
    ):
        """Test LM Studio server up - no error."""
        config = Config()
        config.set_backend("lmstudio")
        console = Console()
        logger = MagicMock()

        # Mock successful connection
        mock_sock_instance = Mock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock_instance

        # Should not raise
        client = OpenAIGenericClient(config, console, logger)
        assert client is not None

    @patch("openai.OpenAI")
    def test_cloud_providers_skip_check(self, mock_openai):
        """Test cloud providers skip server check."""
        config = Config()
        console = Console()
        logger = MagicMock()

        # Test OpenAI - should not check socket
        config.set_backend("openai")
        with patch("socket.socket") as mock_socket:
            OpenAIGenericClient(config, console, logger)
            # Socket should not be called
            mock_socket.assert_not_called()
