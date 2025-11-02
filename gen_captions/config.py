"""A module to manage the configuration of the application.

It encapsulates the configuration settings for the application.
"""

import os
import pkgutil
from typing import Any, Dict, Optional

from .config_manager import ConfigManager


class Config:
    """Application configuration with YAML backend.

    This class manages configuration loaded from YAML files
    with environment variables for API keys only.

    Configuration sources:
    1. YAML files (default.yaml + local overrides)
    2. Environment variables (API keys only)
    """

    def __init__(
        self, config_manager: Optional[ConfigManager] = None
    ):
        """Initialize configuration from YAML."""
        from rich.console import Console

        self._console = Console()
        self._config_manager = config_manager or ConfigManager(
            self._console
        )

        # Load VERSION
        ver = pkgutil.get_data(__name__, "VERSION")
        ver = (
            ver.decode("utf-8").strip() if ver else "0.0.0"
        )
        self._version = ver

        # Load YAML configuration
        self._yaml_config = self._config_manager.get_config()

        # Validate config
        errors = self._config_manager.validate_config(
            self._yaml_config
        )
        if errors:
            self._console.print(
                "[bold yellow]Configuration "
                "validation warnings:[/]"
            )
            for error in errors:
                self._console.print(f"  - {error}")
            # Continue with warnings for usability

        # Runtime state (set by set_backend)
        self._llm_api_key: Optional[str] = None
        self._llm_model: Optional[str] = None
        self._llm_base_url: Optional[str] = None
        self._current_backend: Optional[str] = None

    @property
    def VERSION(self) -> str:
        """Return application version."""
        return self._version

    @property
    def LLM_API_KEY(self) -> Optional[str]:
        """Return LLM API key (always from environment)."""
        return self._llm_api_key

    @property
    def LLM_MODEL(self) -> Optional[str]:
        """Return LLM model name."""
        return self._llm_model

    @property
    def LLM_BASE_URL(self) -> Optional[str]:
        """Return LLM base URL."""
        return self._llm_base_url

    @property
    def THREAD_POOL(self) -> int:
        """Return thread pool size from YAML."""
        return self._yaml_config.get("processing", {}).get(
            "thread_pool", 10
        )

    @property
    def THROTTLE_RETRIES(self) -> int:
        """Return throttle retries from YAML."""
        return self._yaml_config.get("processing", {}).get(
            "throttle_retries", 10
        )

    @property
    def THROTTLE_BACKOFF_FACTOR(self) -> float:
        """Return backoff factor from YAML."""
        return self._yaml_config.get("processing", {}).get(
            "throttle_backoff_factor", 2.0
        )

    @property
    def LOG_LEVEL(self) -> str:
        """Return log level from YAML."""
        return self._yaml_config.get("processing", {}).get(
            "log_level", "INFO"
        )

    @property
    def THROTTLE_SUBMISSION_RATE(self) -> float:
        """Return submission rate from YAML."""
        return self._yaml_config.get("processing", {}).get(
            "throttle_submission_rate", 1.0
        )

    def set_backend(self, backend: str):
        """Set active model profile and load its configuration.

        Args:
            backend: Model profile name (e.g., 'openai', 'grok')
        """
        backend = backend.lower().strip()
        self._current_backend = backend

        # Get profile config from YAML
        backends = self._yaml_config.get("backends", {})
        backend_config = backends.get(backend)

        if not backend_config:
            self._console.print(
                f"[bold red]Error:[/] Unknown model profile: "
                f"{backend}"
            )
            self._console.print(
                f"Available profiles: "
                f"{', '.join(backends.keys())}"
            )
            return

        # API key ALWAYS from environment (security)
        backend_upper = backend.upper()
        self._llm_api_key = os.getenv(
            f"{backend_upper}_API_KEY"
        )

        if not self._llm_api_key:
            self._console.print(
                f"[bold yellow]Warning:[/] "
                f"{backend_upper}_API_KEY not set"
            )

        # Model and base_url from YAML only
        self._llm_model = backend_config.get("model")
        self._llm_base_url = backend_config.get("base_url")

    def get_caption_config(self) -> Dict[str, Any]:
        """Get caption generation configuration.

        Returns:
            Dictionary with caption configuration
        """
        return self._yaml_config.get("caption", {})

    def get_version(self):
        """Return the current version."""
        return self.VERSION
