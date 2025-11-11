"""Application configuration loading and helpers."""

import os
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Dict, Optional, cast

import tomllib

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

        self._version = self._load_version()

        # Load YAML configuration
        self._yaml_config: Dict[str, Any] = (
            self._config_manager.get_config()
        )

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
        processing = self._get_processing_config()
        value = processing.get("thread_pool", 10)
        return int(value)

    @property
    def THROTTLE_RETRIES(self) -> int:
        """Return throttle retries from YAML."""
        processing = self._get_processing_config()
        value = processing.get("throttle_retries", 10)
        return int(value)

    @property
    def THROTTLE_BACKOFF_FACTOR(self) -> float:
        """Return backoff factor from YAML."""
        processing = self._get_processing_config()
        value = processing.get("throttle_backoff_factor", 2.0)
        return float(value)

    @property
    def LOG_LEVEL(self) -> str:
        """Return log level from YAML."""
        processing = self._get_processing_config()
        level = processing.get("log_level", "INFO")
        return str(level)

    @property
    def THROTTLE_SUBMISSION_RATE(self) -> float:
        """Return submission rate from YAML."""
        processing = self._get_processing_config()
        value = processing.get("throttle_submission_rate", 1.0)
        return float(value)

    def set_backend(self, backend: str):
        """Set active model profile and load its configuration.

        Args:
            backend: Model profile name (e.g., 'openai', 'grok',
                     'lmstudio', 'ollama')
        """
        backend = backend.lower().strip()
        self._current_backend = backend

        # Get profile config from YAML
        backends = self._yaml_config.get("backends", {})
        backend_config = backends.get(backend)

        if not isinstance(backend_config, dict):
            self._console.print(
                f"[bold red]Error:[/] Unknown model profile: "
                f"{backend}"
            )
            self._console.print(
                f"Available profiles: "
                f"{', '.join(backends.keys())}"
            )
            return

        # API key handling: local providers don't need keys
        backend_upper = backend.upper()
        if backend in ("lmstudio", "ollama"):
            # Local providers use backend name as placeholder
            self._llm_api_key = backend
            self._console.print(
                f"[blue]Info:[/] Using local provider '{backend}' "
                f"(no API key required)"
            )
        else:
            # Cloud providers require API keys from environment
            self._llm_api_key = os.getenv(
                f"{backend_upper}_API_KEY"
            )

            if not self._llm_api_key:
                self._console.print(
                    f"[bold yellow]Warning:[/] "
                    f"{backend_upper}_API_KEY not set"
                )

        # Model and base_url from YAML only
        self._llm_model = cast(
            Optional[str], backend_config.get("model")
        )
        self._llm_base_url = cast(
            Optional[str], backend_config.get("base_url")
        )

        # Show configuration
        self._console.print(
            f"[green]✓[/] Model profile set to: {backend}"
        )
        self._console.print(f"  Model: {self._llm_model}")
        self._console.print(f"  Base URL: {self._llm_base_url}")

    def get_caption_config(self) -> Dict[str, Any]:
        """Get caption generation configuration.

        Returns:
            Dictionary with caption configuration
        """
        caption = self._yaml_config.get("caption", {})
        return caption if isinstance(caption, dict) else {}

    def get_removal_config(self) -> Dict[str, Any]:
        """Get removal analysis configuration."""
        removal = self._yaml_config.get("removal", {})
        return removal if isinstance(removal, dict) else {}

    def get_removal_thresholds(self) -> Dict[str, float]:
        """Return normalized probability thresholds for removal decisions."""
        removal_cfg = self.get_removal_config()
        raw_default = removal_cfg.get("decision_threshold", 0.9)
        default_threshold = self._coerce_probability(
            raw_default, 0.9
        )

        thresholds_raw = removal_cfg.get("thresholds", {}) or {}
        thresholds_src = (
            thresholds_raw
            if isinstance(thresholds_raw, dict)
            else {}
        )
        normalized: Dict[str, float] = {
            key: self._coerce_probability(
                value, default_threshold
            )
            for key, value in thresholds_src.items()
        }

        for key in ("is_solo_p", "is_woman_p", "is_man_p"):
            normalized.setdefault(key, default_threshold)

        return normalized

    @staticmethod
    def _coerce_probability(
        value: Any, fallback: float
    ) -> float:
        """Convert raw probability inputs into [0, 1] floats."""
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return fallback

        if numeric < 0:
            return 0.0
        if numeric > 1:
            return 1.0
        return numeric

    def _get_processing_config(self) -> Dict[str, Any]:
        processing = self._yaml_config.get("processing", {})
        return processing if isinstance(processing, dict) else {}

    def get_version(self):
        """Return the current version."""
        return self.VERSION

    def _load_version(self) -> str:
        """Return package version using pyproject metadata as the source."""
        try:
            return importlib_metadata.version("gen-captions")
        except importlib_metadata.PackageNotFoundError:
            return self._load_version_from_pyproject()
        except Exception:
            return "0.0.0"

    def _load_version_from_pyproject(self) -> str:
        project_root = Path(__file__).resolve().parent.parent
        pyproject_path = project_root / "pyproject.toml"
        if not pyproject_path.exists():
            return "0.0.0"

        try:
            with pyproject_path.open("rb") as handle:
                data = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError):
            return "0.0.0"

        project_section = data.get("project", {})
        version = project_section.get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()
        return "0.0.0"
