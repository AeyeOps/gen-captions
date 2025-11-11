"""Configuration schema definitions and validation.

This module defines the structure and validation logic for the
application's YAML configuration files.
"""

from dataclasses import dataclass
from typing import Any, Dict

CONFIG_VERSION = "1.0"  # For future migrations


@dataclass
class ModelConfig:
    """Model-specific configuration for LLM quirks.

    Different models have different capabilities and parameter
    requirements. This class encapsulates those differences.
    """

    supports_system_role: bool = True
    supports_temperature: bool = True
    max_tokens_key: str = "max_completion_tokens"
    max_tokens_value: int = 200

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelConfig":
        """Create ModelConfig from dictionary."""
        return cls(
            supports_system_role=data.get(
                "supports_system_role", True
            ),
            supports_temperature=data.get(
                "supports_temperature", True
            ),
            max_tokens_key=data.get(
                "max_tokens_key", "max_completion_tokens"
            ),
            max_tokens_value=data.get("max_tokens_value", 200),
        )


@dataclass
class ProcessingConfig:
    """Processing and throttling settings."""

    thread_pool: int = 10
    throttle_submission_rate: float = 1.0
    throttle_retries: int = 10
    throttle_backoff_factor: float = 2.0
    log_level: str = "INFO"

    def validate(self) -> list[str]:
        """Return list of validation errors."""
        errors = []
        if self.thread_pool < 1:
            errors.append("thread_pool must be >= 1")
        if self.throttle_submission_rate <= 0:
            errors.append("throttle_submission_rate must be > 0")
        if self.throttle_retries < 0:
            errors.append("throttle_retries must be >= 0")
        if self.throttle_backoff_factor < 1:
            errors.append("throttle_backoff_factor must be >= 1")
        valid_levels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        if self.log_level not in valid_levels:
            errors.append(f"invalid log_level: {self.log_level}")
        return errors

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any]
    ) -> "ProcessingConfig":
        """Create ProcessingConfig from dictionary."""
        return cls(
            thread_pool=data.get("thread_pool", 10),
            throttle_submission_rate=data.get(
                "throttle_submission_rate", 1.0
            ),
            throttle_retries=data.get("throttle_retries", 10),
            throttle_backoff_factor=data.get(
                "throttle_backoff_factor", 2.0
            ),
            log_level=data.get("log_level", "INFO"),
        )


@dataclass
class BackendConfig:
    """Backend-specific configuration."""

    model: str
    base_url: str
    models: Dict[str, ModelConfig]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackendConfig":
        """Create BackendConfig from dictionary."""
        models_dict = data.get("models", {})
        models = {
            name: ModelConfig.from_dict(config)
            for name, config in models_dict.items()
        }
        return cls(
            model=data.get("model", ""),
            base_url=data.get("base_url", ""),
            models=models,
        )
