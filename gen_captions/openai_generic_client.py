"""Utilities for calling OpenAI-compatible caption models."""

# pylint: disable=duplicate-code

import time
from logging import Logger

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
        "supports_temperature": True,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 300,
    },
    "gpt-5": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 300,
    },
    "gpt-5-nano": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_completion_tokens",
        "max_tokens_value": 200,
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
        "max_tokens_value": 500,
    },
    "mistralai/magistral-small-2509": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    # === Ollama Models ===
    "qwen2.5vl:7b": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    "minicpm-o-2.6:latest": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
    },
    "openbmb/minicpm-o2.6:latest": {
        "supports_system_role": True,
        "supports_temperature": True,
        "max_tokens_key": "max_tokens",
        "max_tokens_value": 250,
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
                payload = self._build_chat_request(base64_image)
                response = self._client.chat.completions.create(
                    **payload
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
                if (
                    isinstance(re, openai.APIConnectionError)
                    and re.code
                ):
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

    def _build_chat_request(self, base64_image: str) -> dict:
        """Build request parameters with model quirks."""
        model_name = self._config.LLM_MODEL.strip().lower()

        # Get model quirks from hardcoded config
        model_quirks = MODEL_CONFIG.get(model_name, {})

        # Get caption prompts from YAML
        caption_config = self._config.get_caption_config()
        system_content = caption_config.get(
            "system_prompt", ""
        ).strip()
        user_prompt = caption_config.get(
            "user_prompt", ""
        ).strip()

        # Default request params
        request_params = {"model": self._config.LLM_MODEL}

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

        # Use the model-specific param for max tokens
        request_params[str(max_tokens_key)] = max_tokens_value

        return request_params
