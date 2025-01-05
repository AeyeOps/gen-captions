import time
import os
import requests
from openai import OpenAI, APIConnectionError, RateLimitError

from . import config
from .logger_config import logger
from .utils import encode_image


class OpenAIGenericClient:
    """OpenAI generic API client for interacting with both OpenAI and Grok to generate image descriptions."""

    def __init__(self):
        self.client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)

    def generate_description(self, image_path: str) -> str:
        """Generate a description for the image using the OpenAI API."""
        logger.info(f"Processing image with LLM: {image_path}")
        base64_image = encode_image(image_path)
        retries = 0

        while retries < config.THROTTLE_RETRIES:
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    temperature=0.1,
                    max_tokens=200,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert at generating detailed and accurate stability diffusion type prompts."
                                " You emphasize photo realism and accuracy in your captions."
                            ),
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """
                                        Describe the content of this image as a detailed and accurate caption for a stable
                                        diffusion model prompt and begin the response with one of two opening lines based on 
                                        the gender of the person in the image. 
                                        
                                        If the person is woman, start the response with:
                                        [trigger], a woman, 
                                        
                                        If the person is a man, start the response with:
                                        
                                        The caption should be short, concise and accurate, and should not contain any information
                                        not imediately descriptive of the image. Avoid all words with single quotes, double quotes, 
                                        or any other special characters.
                                    """,
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        },
                    ],
                )
                if response and response.choices:
                    return response.choices[0].message.content.strip()
                return ""
            except RateLimitError as rle:
                if rle.response.status_code == 429:
                    retries += 1
                    wait_time = config.THROTTLE_BACKOFF_FACTOR**retries
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error occurred: {rle}")
                    break

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retries += 1
                    wait_time = config.THROTTLE_BACKOFF_FACTOR**retries
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error occurred: {e}")
                    break

            except APIConnectionError as ce:
                retries += 1
                wait_time = config.THROTTLE_BACKOFF_FACTOR**retries
                logger.warning(
                    f"API connection error. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                break

        return ""
