"""YAML configuration file management.

This module manages loading, merging, and saving YAML
configurations for the application.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

from .config_schema import CONFIG_VERSION, ProcessingConfig


class ConfigManager:
    """Manages loading, merging, and saving YAML configs."""

    CONFIG_SEARCH_PATHS = [
        Path.home() / ".config" / "gen-captions" / "config.yaml",
        Path.cwd() / "gen-captions.yaml",
        Path.cwd() / ".gen-captions.yaml",
    ]

    def __init__(self, console: Optional[Console] = None):
        """Initialize configuration manager."""
        self.console = console or Console()
        self._default_config: Optional[Dict[str, Any]] = None
        self._local_config: Optional[Dict[str, Any]] = None
        self._merged_config: Optional[Dict[str, Any]] = None

    def get_default_config_path(self) -> Path:
        """Return path to bundled default.yaml."""
        # Use path relative to this module
        # Works both in dev and PyInstaller binary
        return Path(__file__).parent / "default.yaml"

    def load_default_config(self) -> Dict[str, Any]:
        """Load bundled default configuration."""
        if self._default_config is not None:
            return self._default_config

        config_path = self.get_default_config_path()

        try:
            with open(
                config_path, "r", encoding="utf-8"
            ) as f:
                self._default_config = yaml.safe_load(f)
            return self._default_config
        except FileNotFoundError:
            self.console.print(
                f"[bold red]Error:[/] Default config not "
                f"found: {config_path}"
            )
            # Return minimal fallback
            return self._get_fallback_config()
        except yaml.YAMLError as e:
            self.console.print(
                f"[bold red]Error parsing default "
                f"config:[/] {e}"
            )
            return self._get_fallback_config()

    def find_local_config(self) -> Optional[Path]:
        """Find local config file using search paths."""
        # Check explicit override
        override = os.getenv("GEN_CAPTIONS_CONFIG")
        if override:
            path = Path(override).expanduser()
            if path.exists():
                return path
            self.console.print(
                f"[yellow]Warning:[/] GEN_CAPTIONS_CONFIG "
                f"points to non-existent file: {path}"
            )

        # Search standard paths
        for path in self.CONFIG_SEARCH_PATHS:
            if path.exists():
                return path

        return None

    def load_local_config(self) -> Dict[str, Any]:
        """Load local configuration file if it exists."""
        if self._local_config is not None:
            return self._local_config

        config_path = self.find_local_config()
        if not config_path:
            return {}

        try:
            with open(
                config_path, "r", encoding="utf-8"
            ) as f:
                self._local_config = yaml.safe_load(f) or {}
            return self._local_config
        except yaml.YAMLError as e:
            self.console.print(
                f"[bold red]Error parsing local "
                f"config:[/] {e}"
            )
            self.console.print(
                "[yellow]Falling back to default config[/]"
            )
            return {}

    def merge_configs(
        self,
        default: Dict[str, Any],
        local: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deep merge local config over default config."""
        merged = default.copy()

        for key, value in local.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self.merge_configs(
                    merged[key], value
                )
            else:
                merged[key] = value

        return merged

    def get_config(self) -> Dict[str, Any]:
        """Get merged configuration (default + local)."""
        if self._merged_config is not None:
            return self._merged_config

        default = self.load_default_config()
        local = self.load_local_config()

        self._merged_config = self.merge_configs(default, local)
        return self._merged_config

    def validate_config(
        self, config: Dict[str, Any]
    ) -> list[str]:
        """Validate configuration and return errors."""
        errors = []

        # Check version compatibility
        config_version = config.get(
            "config_version", "unknown"
        )
        if config_version != CONFIG_VERSION:
            errors.append(
                f"Config version mismatch: got "
                f"{config_version}, expected {CONFIG_VERSION}"
            )

        # Validate processing section
        if "processing" in config:
            try:
                proc_config = ProcessingConfig.from_dict(
                    config["processing"]
                )
                errors.extend(proc_config.validate())
            except (TypeError, KeyError) as e:
                errors.append(
                    f"Invalid processing config: {e}"
                )
        else:
            errors.append("Missing 'processing' section")

        # Validate backends section
        if "backends" not in config:
            errors.append("Missing 'backends' section")
        else:
            backends = config["backends"]
            if not isinstance(backends, dict):
                errors.append("'backends' must be a dict")
            elif len(backends) == 0:
                errors.append(
                    "'backends' section is empty"
                )

        return errors

    def create_local_config_template(
        self, output_path: Optional[Path] = None
    ) -> Path:
        """Create a local config template file."""
        if output_path is None:
            # Use first search path (user config dir)
            output_path = self.CONFIG_SEARCH_PATHS[0]

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a minimal template (not a full copy)
        template = self._create_minimal_template()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)

        # Set secure permissions (user read/write only)
        output_path.chmod(0o600)

        return output_path

    def _create_minimal_template(self) -> str:
        """Create minimal template with common overrides."""
        return """# gen-captions Local Configuration
# This file overrides settings from default.yaml
# Only include settings you want to customize
#
# API Keys: Set via environment variables (NOT in this file)
#   export OPENAI_API_KEY=sk-...
#   export GROK_API_KEY=xai-...
#
# Documentation: https://github.com/AeyeOps/gen-captions

config_version: "1.0"

# Uncomment and modify sections below as needed

# processing:
#   thread_pool: 20
#   throttle_submission_rate: 2.0
#   throttle_retries: 15
#   log_level: DEBUG

# backends:
#   openai:
#     model: gpt-5
#   grok:
#     model: grok-2-vision-1212
"""

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Return minimal hardcoded fallback config."""
        return {
            "config_version": CONFIG_VERSION,
            "processing": {
                "thread_pool": 10,
                "throttle_submission_rate": 1.0,
                "throttle_retries": 10,
                "throttle_backoff_factor": 2.0,
                "log_level": "INFO",
            },
            "backends": {
                "openai": {
                    "model": "gpt-5-mini",
                    "base_url": "https://api.openai.com/v1",
                },
                "grok": {
                    "model": "grok-2-vision-1212",
                    "base_url": "https://api.x.ai/v1",
                },
            },
            "caption": {
                "required_token": "[trigger]",
                "system_prompt": (
                    "You are an expert at generating "
                    "detailed and accurate stability "
                    "diffusion type prompts."
                ),
                "user_prompt": (
                    "Describe the content of this image..."
                ),
            },
        }

    def set_config_value(
        self, key_path: str, value: Any
    ) -> None:
        """Set a configuration value in local config.

        Args:
            key_path: Dot-notation path (e.g.,
                     'processing.thread_pool')
            value: Value to set
        """
        local_path = self.find_local_config()

        if not local_path:
            raise FileNotFoundError(
                "No local config found. "
                "Run 'gen-captions config init' first"
            )

        # Load current local config
        with open(local_path, "r", encoding="utf-8") as f:
            local_config = yaml.safe_load(f) or {}

        # Navigate to the nested key and set value
        keys = key_path.split(".")
        current = local_config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Convert value to appropriate type
        current[keys[-1]] = self._parse_value(value)

        # Write back to file
        with open(local_path, "w", encoding="utf-8") as f:
            yaml.dump(
                local_config,
                f,
                default_flow_style=False,
                sort_keys=False,
            )

        # Clear cached configs to force reload
        self._local_config = None
        self._merged_config = None

    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        # Try to parse as YAML to handle bools, ints, etc.
        try:
            return yaml.safe_load(value)
        except yaml.YAMLError:
            # Return as string if parsing fails
            return value
