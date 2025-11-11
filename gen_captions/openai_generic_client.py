"""Utilities for calling OpenAI-compatible caption models."""

# pylint: disable=duplicate-code

import json
import re
import time
from logging import Logger
from typing import Any, Dict, Optional

import openai
from requests import HTTPError
from rich.console import Console

from .config import Config
from .utils import encode_image

# Model-specific quirks and parameter requirements
# This dict captures how different models handle API parameters
MODEL_CONFIG = {
    "o1-mini": {
        "supports_system_role": False,
        "supports_temperature": False,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 200,
    },
    "o3-mini": {
        "supports_system_role": True,
        "supports_temperature": False,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "gpt-5-mini": {
        "supports_system_role": True,
        "supports_temperature": False,
        "reasoning_effort": "medium",
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 2000,
    },
    "gpt-5": {
        "supports_system_role": True,
        "supports_temperature": False,
        "reasoning_effort": "medium",
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 2000,
    },
    "gpt-5-nano": {
        "supports_system_role": True,
        "supports_temperature": False,
        "reasoning_effort": "medium",
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 2000,
    },
    "gpt-4o-mini": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 200,
    },
    "gpt-4o": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 200,
    },
    "grok-2-vision-1212": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    "grok-vision-beta": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    # === LM Studio Models ===
    "qwen/qwen3-vl-8b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 300,
    },
    "qwen/qwen2.5-vl-7b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    "google/gemma-3-27b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 256,
    },
    "mistralai/magistral-small-2509": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    # === Ollama Models ===
    # MiniCPM (openbmb)
    "openbmb/minicpm-v4.5": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "openbmb/minicpm-o2.6": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "openbmb/minicpm-v4": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "openbmb/minicpm-v2.6": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "openbmb/minicpm-v2.5": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    # Qwen
    "qwen2.5vl:7b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    "qwen2.5vl:3b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    # LLaVA
    "llava:7b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "llava-llama3:8b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "llava-phi3:3.8b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    "bakllava:7b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 200,
    },
    # Moondream
    "moondream:1.8b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 150,
    },
}


class OpenAIGenericClient:
    """Client that wraps OpenAI-compatible chat endpoints."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self, config: Config, console: Console, logger: Logger
    ):
        """Initialize the OpenAI client with API key and URL."""
        if not config.LLM_API_KEY:
            logger.error(
                "LLM_API_KEY is not set. "
                "Requests to the API will fail."
            )

        if not config.LLM_MODEL:
            logger.warning("LLM_MODEL is not configured")

        if not config.LLM_BASE_URL:
            logger.warning("LLM_BASE_URL is not configured")

        self._client = openai.OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
        )
        self._config = config
        self._console = console
        self._logger = logger

        # Verify local server availability for lmstudio/ollama
        self._verify_local_server_availability()

    def _verify_local_server_availability(self) -> bool:
        """Verify local server is running for lmstudio/ollama backends.

        Returns:
            True if server is reachable, False otherwise

        Raises:
            ConnectionError: If server is not available
                (backend-specific message)
        """
        import socket
        import urllib.parse

        # Only check local providers
        backend = self._config._current_backend
        if backend not in ("lmstudio", "ollama"):
            return True

        # Parse base URL to extract host and port
        parsed_url = urllib.parse.urlparse(
            self._config.LLM_BASE_URL
        )
        hostname = parsed_url.hostname or "localhost"
        # Ensure hostname is str, not bytes
        host = (
            hostname.decode()
            if isinstance(hostname, bytes)
            else hostname
        )
        port = parsed_url.port

        if not port:
            # Default ports if not specified
            port = 1234 if backend == "lmstudio" else 11434

        # Attempt socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout

        try:
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                # Server not reachable - raise backend-specific error
                self._raise_server_not_running_error(
                    backend, host, port
                )

            return True

        except socket.error as e:
            self._logger.error(
                "Socket error checking %s server: %s", backend, e
            )
            self._raise_server_not_running_error(
                backend, host, port
            )

        return False

    def _raise_server_not_running_error(
        self, backend: str, host: str, port: int
    ) -> None:
        """Raise backend-specific connection error with helpful message.

        Args:
            backend: The backend name (lmstudio or ollama)
            host: Server host
            port: Server port
        """
        base_url = f"http://{host}:{port}"

        if backend == "lmstudio":
            msg = (
                f"\n[bold red]LM Studio Server Not Running[/]\n"
                f"\nThe LM Studio server is not reachable at {base_url}\n"
                f"\n[bold yellow]To fix this:[/]"
                f"\n  1. Open LM Studio application"
                f"\n  2. Go to 'Local Server' tab (left sidebar)"
                f"\n  3. Click 'Start Server' button"
                f"\n  4. Ensure port is set to {port}"
                f"\n  5. Load a vision-capable model in the server"
                f"\n\n[dim]For more help, see: "
                f"https://github.com/lmstudio-ai/docs[/]"
            )
        else:  # ollama
            msg = (
                f"\n[bold red]Ollama Server Not Running[/]\n"
                f"\nThe Ollama server is not reachable at {base_url}\n"
                f"\n[bold yellow]To fix this:[/]"
                f"\n  1. Start Ollama server: [cyan]ollama serve[/]"
                f"\n  2. Ensure the server is running "
                f"on port {port}"
                f"\n  3. Pull a vision model: "
                f"[cyan]ollama pull qwen2.5vl:7b[/]"
                f"\n\n[dim]For more help, see: "
                f"https://github.com/ollama/ollama[/]"
            )

        self._console.print(msg)
        self._logger.error(
            "%s server not reachable at %s:%s",
            backend,
            host,
            port,
        )

        raise ConnectionError(
            f"{backend.upper()} server not running at {base_url}. "
            f"See error message above for instructions."
        )

    def generate_description(self, image_path: str) -> str:
        """Generate a description for the image using the OpenAI API.

        Retries if:
        - We hit a rate limit or transient error (429, etc.)
        - The model returns a description that does NOT contain '[trigger]'
        """
        # pylint: disable=broad-except
        self._logger.info(
            "Processing image with LLM: %s", image_path
        )
        self._console.print(
            f"[green]Generating description for:[/] [italic]{image_path}[/]"
        )

        base64_image = encode_image(image_path)
        retries = 0

        while retries < self._config.THROTTLE_RETRIES:
            try:
                # Build request params dynamically
                payload = self._build_chat_request(
                    base64_image,
                    self._config.get_caption_config(),
                )
                response = self._client.chat.completions.create(  # type: ignore[call-overload]
                    **payload
                )

                # Debug: Log raw response
                self._logger.debug(f"API Response: {response}")
                self._logger.debug(
                    f"Response type: {type(response)}"
                )
                if hasattr(response, "choices"):
                    self._logger.debug(
                        f"Choices: {response.choices}"
                    )
                    if (
                        response.choices
                        and len(response.choices) > 0
                    ):
                        self._logger.debug(
                            f"First choice: {response.choices[0]}"
                        )
                        if hasattr(
                            response.choices[0], "message"
                        ):
                            self._logger.debug(
                                f"Message: {response.choices[0].message}"
                            )
                            if hasattr(
                                response.choices[0].message,
                                "content",
                            ):
                                self._logger.debug(
                                    f"Content: {response.choices[0].message.content}"
                                )

                # Check response validity
                if (
                    response
                    and response.choices
                    and response.choices[0]
                    and response.choices[0].message
                    and response.choices[0].message.content
                ):
                    description: str = response.choices[
                        0
                    ].message.content.strip()

                    # If the model didn't produce anything, treat as no content
                    if not description:
                        self._console.print(
                            f"[yellow]No content returned by LLM for:[/]"
                            f" {image_path}"
                        )
                        return ""

                    # Check if [trigger] is in the description
                    if "[trigger]" not in description:
                        # Instead of returning partial, treat as failure/retry
                        self._logger.info(
                            r"Missing \[trigger] token for %s. Retrying...",
                            image_path,
                        )
                        self._console.print(
                            rf"[bold yellow]No \[trigger] token in response "
                            rf"for {image_path}, retrying...[/]"
                        )
                        # Optional short sleep or backoff
                        time.sleep(1)
                        retries += 1
                        continue  # Try again

                    # If we do have [trigger], success
                    self._console.print(
                        "[bold green]Generated description "
                        rf"for:[/] [italic]{image_path}[/]"
                    )
                    return description

                self._console.print(
                    f"[yellow]No content returned by LLM for:[/] {image_path}"
                )
                return ""

            except (
                openai.RateLimitError,
                HTTPError,
                openai.APIConnectionError,
            ) as re:
                # Handle known API-limiting / request errors
                code = 0
                if isinstance(re, openai.APIConnectionError):
                    # Check for connection refusal
                    if "Connection refused" in str(
                        re
                    ) or "Failed to connect" in str(re):
                        backend = self._config._current_backend
                        if backend in ("lmstudio", "ollama"):
                            # Server went down during processing
                            import urllib.parse

                            parsed_url = urllib.parse.urlparse(
                                self._config.LLM_BASE_URL
                            )
                            hostname = (
                                parsed_url.hostname
                                or "localhost"
                            )
                            # Ensure hostname is str
                            host = (
                                hostname.decode()
                                if isinstance(hostname, bytes)
                                else hostname
                            )
                            port = parsed_url.port or (
                                1234
                                if backend == "lmstudio"
                                else 11434
                            )
                            self._raise_server_not_running_error(
                                backend, host, port
                            )

                    if re.code:
                        code = int(re.code)
                elif isinstance(re, openai.RateLimitError):
                    code = re.status_code
                elif isinstance(re, HTTPError):
                    code = re.response.status_code

                if code == 429:
                    wait_time = (
                        self._config.THROTTLE_BACKOFF_FACTOR
                        ** (retries + 1)
                    )
                    self._logger.warning(
                        "Rate limit exceeded. Retrying in %s seconds...",
                        wait_time,
                    )
                    self._console.print(
                        f"[bold yellow]Rate limit for {image_path}, "
                        f"retrying in {wait_time} second(s)...[/]"
                    )
                    time.sleep(wait_time)
                    retries += 1
                else:
                    self._logger.error(
                        "API or HTTP error for %s: %s",
                        image_path,
                        re,
                    )
                    self._console.print(
                        f"[red]API/HTTP error for {image_path}: {re}[/]"
                    )
                    break

            except Exception as e:
                self._logger.exception(
                    "Error generating description: %s", e
                )
                self._console.print(
                    f"[bold red]Error generating description "
                    f" for {image_path}: {e}[/]"
                )
                break

        # If we exit the loop, we either exhausted retries or had a fatal error
        self._console.print(
            (
                "[bold red]Failed to generate description ",
                f"after {retries} retries for {image_path}[/]",
            )
        )
        return ""

    def generate_removal_metadata(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """Return structured metadata used to decide if an image is removed."""
        # pylint: disable=broad-except
        self._logger.info(
            "Analyzing image for removal criteria: %s",
            image_path,
        )
        base64_image = encode_image(image_path)
        retries = 0

        removal_config = dict(
            self._config.get_removal_config() or {}
        )
        self._logger.debug(
            "[Removal] prompts for %s | system=%s | user=%s",
            image_path,
            removal_config.get("system_prompt", "")[:200],
            removal_config.get("user_prompt", "")[:200],
        )

        while retries < self._config.THROTTLE_RETRIES:
            try:
                payload = self._build_chat_request(
                    base64_image, removal_config
                )
                response = self._client.chat.completions.create(  # type: ignore[call-overload]
                    **payload
                )

                if (
                    response
                    and response.choices
                    and response.choices[0]
                    and response.choices[0].message
                    and response.choices[0].message.content
                ):
                    content = response.choices[
                        0
                    ].message.content.strip()
                    self._logger.debug(
                        "[Removal] raw response for %s: %s",
                        image_path,
                        content,
                    )
                    metadata = self._parse_removal_response(
                        content
                    )
                    if metadata:
                        self._logger.debug(
                            "[Removal] parsed metadata for %s: %s",
                            image_path,
                            metadata,
                        )
                        return metadata

                    self._logger.info(
                        "Structured response missing or invalid JSON for %s",
                        image_path,
                    )
                    self._logger.warning(
                        "[Removal] Could not parse response for %s: %s",
                        image_path,
                        content,
                    )
                    retries += 1
                    time.sleep(1)
                    continue

                self._logger.warning(
                    "[Removal] Empty response body for %s", image_path
                )
                return {}

            except (
                openai.RateLimitError,
                HTTPError,
                openai.APIConnectionError,
            ) as re:
                code = 0
                if isinstance(re, openai.APIConnectionError):
                    if "Connection refused" in str(
                        re
                    ) or "Failed to connect" in str(re):
                        backend = self._config._current_backend
                        if backend in ("lmstudio", "ollama"):
                            import urllib.parse

                            parsed_url = urllib.parse.urlparse(
                                self._config.LLM_BASE_URL
                            )
                            hostname = (
                                parsed_url.hostname
                                or "localhost"
                            )
                            host = (
                                hostname.decode()
                                if isinstance(hostname, bytes)
                                else hostname
                            )
                            port = parsed_url.port or (
                                1234
                                if backend == "lmstudio"
                                else 11434
                            )
                            self._raise_server_not_running_error(
                                backend, host, port
                            )

                    if re.code:
                        code = int(re.code)
                elif isinstance(re, openai.RateLimitError):
                    code = re.status_code
                elif isinstance(re, HTTPError):
                    code = re.response.status_code

                if code == 429:
                    wait_time = (
                        self._config.THROTTLE_BACKOFF_FACTOR
                        ** (retries + 1)
                    )
                    self._logger.warning(
                        (
                            "Rate limit exceeded during removal analysis. "
                            "Retrying in %s seconds..."
                        ),
                        wait_time,
                    )
                    self._console.print(
                        (
                            "[bold yellow]Rate limit for "
                            f"{image_path}, retrying in {wait_time} second(s)...[/]"
                        )
                    )
                    time.sleep(wait_time)
                    retries += 1
                else:
                    self._logger.error(
                        "API/HTTP error during removal analysis for %s: %s",
                        image_path,
                        re,
                    )
                    if (
                        code == 400
                        and "model has crashed" in str(re).lower()
                    ):
                        crash_msg = (
                            "Local model reported a crash. Restart the LM Studio server "
                            "(Local Server tab → Stop → Start) and rerun this command."
                        )
                        self._logger.error(crash_msg)
                        break
                    self._console.print(
                        f"[red]API/HTTP error for {image_path}: {re}[/]"
                    )
                    break

            except (
                Exception
            ) as exc:  # pragma: no cover - defensive logging
                self._logger.exception(
                    "Error generating removal metadata: %s", exc
                )
                self._console.print(
                    f"[bold red]Error generating removal metadata for {image_path}: {exc}[/]"
                )
                break

        self._console.print(
            (
                "[bold red]Failed to analyze removal criteria ",
                f"after {retries} retries for {image_path}[/]",
            )
        )
        return {}

    def _build_chat_request(
        self, base64_image: str, prompt_config: Dict[str, Any]
    ) -> dict[str, object]:
        """Build request parameters with model quirks."""
        model_name = (
            self._config.LLM_MODEL.strip().lower()
            if self._config.LLM_MODEL
            else ""
        )

        # Get model quirks from hardcoded config
        model_quirks = MODEL_CONFIG.get(model_name, {})

        prompt_config = prompt_config or {}
        system_content = prompt_config.get(
            "system_prompt", ""
        ).strip()
        user_prompt = prompt_config.get(
            "user_prompt", ""
        ).strip()

        # Default request params
        request_params: dict[str, object] = {
            "model": self._config.LLM_MODEL
        }

        # Get model quirks (defaults for unknown models)
        supports_system = model_quirks.get(
            "supports_system_role", True
        )
        supports_temp = model_quirks.get(
            "supports_temperature", True
        )
        max_tokens_key = model_quirks.get(
            "max_tokens_key", "max_completion_tokens"
        )
        max_tokens_value = model_quirks.get(
            "max_tokens_value", 200
        )

        # Build messages based on supports_system
        if supports_system:
            messages = [
                {"role": "system", "content": system_content},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ]
        else:
            # Merge system content into user content only
            combined_content = (
                system_content.strip()
                + "\n\n"
                + user_prompt.strip()
            )
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": combined_content,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]

        request_params["messages"] = messages

        # Add temperature if supported
        if supports_temp:
            request_params["temperature"] = 0.1

        # Add reasoning_effort for GPT-5 models
        reasoning_effort = model_quirks.get("reasoning_effort")
        if reasoning_effort:
            request_params["reasoning_effort"] = reasoning_effort

        # Use the model-specific param for max tokens
        request_params[str(max_tokens_key)] = max_tokens_value

        return request_params

    def _parse_removal_response(
        self, content: str
    ) -> Dict[str, Any]:
        """Parse JSON response from the model for removal metadata."""
        parsed = self._extract_json_dict(content)
        if not parsed:
            return {}

        return {
            "thought": str(parsed.get("thought", "")).strip(),
            "is_solo_p": self._clamp_probability(
                parsed.get("is_solo_p")
            ),
            "is_woman_p": self._clamp_probability(
                parsed.get("is_woman_p")
            ),
            "is_man_p": self._clamp_probability(
                parsed.get("is_man_p")
            ),
        }

    @staticmethod
    def _clamp_probability(value: Any) -> float:
        """Normalize probability-like values into the [0, 1] range."""
        try:
            prob = float(value)
        except (TypeError, ValueError):
            return 0.0

        if prob < 0:
            return 0.0
        if prob > 1:
            return 1.0
        return prob

    @staticmethod
    def _extract_json_dict(
        content: str,
    ) -> Optional[Dict[str, Any]]:
        """Extract a JSON object from free-form content."""
        if not content:
            return None
        try:
            loaded = json.loads(content)
            return loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    loaded = json.loads(match.group(0))
                    return (
                        loaded
                        if isinstance(loaded, dict)
                        else None
                    )
                except json.JSONDecodeError:
                    return None
        return None
