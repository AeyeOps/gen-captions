"""OpenAI generic API client for  OpenAI and Grok.

This module provides a generic client for interacting with both OpenAI
and Grok. It is used to generate image descriptions using the OpenAI
API.
"""

import time
from logging import Logger

from openai import APIConnectionError, OpenAI, RateLimitError
from requests import HTTPError
from rich.console import Console

from .config import Config
from .utils import encode_image


class OpenAIGenericClient:
    """OpenAI generic API client for interacting with.

    Both OpenAI and Grok to generate image descriptions.
    """

    def __init__(self, config: Config, console: Console, logger: Logger):
        """Initialize the OpenAI client with the API key and base URL."""
        self._client = OpenAI(
            api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL
        )
        self._config = config
        self._console = console
        self._logger = logger

    def generate_description(self, image_path: str) -> str:
        """Generate a description for the image using the OpenAI API."""
        self._logger.info("Processing image with LLM: %s", image_path)
        base64_image = encode_image(image_path)
        retries = 0

        while retries < self._config.THROTTLE_RETRIES:
            try:
                response = self._client.chat.completions.create(
                    model=self._config.LLM_MODEL,
                    temperature=0.1,
                    max_tokens=200,
                    messages=[
                        {
                            "role": "system",
                            "content": """
You are an expert at generating detailed and 
accurate stability diffusion type prompts. You 
emphasize photo realism and accuracy in your captions.
""",
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """
Describe the content of this image as a 
detailed and accurate caption for a stable diffusion model
prompt and begin the response with one of two opening
lines based on the gender of the person in the image. 
The caption should be short, concise and accurate, 
and should not contain any information not imediately 
descriptive of the image. Avoid all words with single 
quotes, double quotes, or any other special characters.

If the person is woman, start the response with: 
[trigger], a woman, 

If the person is a man, start the response with:
[trigger], a man, 
""",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg"
                                        f";base64,{base64_image}"
                                    },
                                },
                            ],
                        },
                    ],
                )
                if (
                    response
                    and response.choices
                    and response.choices[0]
                    and response.choices[0].message
                    and response.choices[0].message.content
                ):
                    return response.choices[0].message.content.strip()
                return ""
            except (RateLimitError, HTTPError, APIConnectionError) as re:
                code = 0
                if isinstance(re, APIConnectionError):
                    code = int(re.code) if re.code else 0
                elif isinstance(re, RateLimitError):
                    code = re.status_code
                elif isinstance(re, HTTPError):
                    code = re.response.status_code
                if code == 429:
                    wait_time = self._config.THROTTLE_BACKOFF_FACTOR ** (
                        retries + 1
                    )
                    self._logger.warning(
                        "Rate limit exceeded. Retrying in %s seconds...",
                        wait_time,
                    )
                    time.sleep(wait_time)
                    retries += 1
                else:
                    break
            except Exception as e:
                self._logger.exception(
                    "Error generating description: %s", e
                )
                break
        return ""
