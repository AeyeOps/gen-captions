import time
from logging import Logger

from openai import APIConnectionError, OpenAI, RateLimitError
from requests import HTTPError
from rich.console import Console

from .config import Config
from .utils import encode_image

# Example dictionary capturing different model quirks
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
    # Add more models here with their own rules
}


class OpenAIGenericClient:
    """OpenAI generic API client for interacting with.

    Both OpenAI and Grok to generate image descriptions.
    """

    def __init__(
        self, config: Config, console: Console, logger: Logger
    ):
        """Initialize the OpenAI client with the API key and base URL."""
        self._client = OpenAI(
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
                    description = response.choices[
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
                RateLimitError,
                HTTPError,
                APIConnectionError,
            ) as re:
                # Handle known API-limiting / request errors
                code = 0
                if (
                    isinstance(re, APIConnectionError)
                    and re.code
                ):
                    code = int(re.code)
                elif isinstance(re, RateLimitError):
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
        """Dynamically build request parameters based on the model using
        MODEL_CONFIG for known quirks."""
        model_name = self._config.LLM_MODEL.strip().lower()
        model_quirks = MODEL_CONFIG.get(model_name, {})

        # Base content for "system" and "user" roles
        system_content = """
You are an expert at generating detailed and 
accurate stability diffusion type prompts. You 
emphasize photo realism and accuracy in your captions.
"""
        user_prompt = """
Describe the content of this image as a 
detailed and accurate caption for a stable diffusion model
prompt and begin the response with one of two opening
lines based on the gender of the person in the image. 
The caption should be short, concise and accurate, 
and should not contain any information not immediately 
descriptive of the image. Avoid all words with single 
quotes, double quotes, or any other special characters.

If the person is woman, start the response with: 
[trigger], a woman, 

If the person is a man, start the response with:
[trigger], a man, 
"""

        # Default request params
        request_params = {"model": self._config.LLM_MODEL}

        # If model not in dictionary, assume a "normal" model
        # supporting system role, temperature, max_completion_tokens, etc.
        if not model_quirks:
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
            request_params["messages"] = messages
            request_params["temperature"] = 0.1
            request_params["max_completion_tokens"] = 200
            return request_params

        # If we do have quirks
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
