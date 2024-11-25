# gen_captions/openai_api.py

from openai import OpenAI
import time
import os

from .constants import OPENAI_API_KEY, THROTTLE_RETRIES, THROTTLE_BACKOFF_FACTOR
from .logger_config import logger
from .utils import encode_image
import requests

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_description(image_path):
    """Generate a description for the image using the OpenAI API."""
    logger.info(f"Processing image {image_path}...")
    base64_image = encode_image(image_path)
    retries = 0
    while retries < THROTTLE_RETRIES:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=200,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at generating detailed and accurate stability diffusion type prompts. You emphasize photo realism and accuracy in your captions.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """
                                    Describe the content of this image as a detailed and accurate caption for a stable
                                    diffusion model prompt and use [trigger] to identify the primary woman subject. Refer to her as [trigger], a woman.
                                    As early as possible in the prompt for the first time.
                                    Do not capitalize the name regardless of where you place it in the sentence it should always be lowercase [trigger].
                                    Feel free to reference her multiple times in the caption if necessary.
                                    The caption should be concise and accurate, and should not contain any irrelevant information. Avoid all words with
                                    single quotes, double quotes, or any other special characters.
                                    """,
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    },
                ],
            )
            if response and response.choices:
                return response.choices[0].message.content.strip()
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retries += 1
                wait_time = THROTTLE_BACKOFF_FACTOR ** retries
                logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP error occurred: {e}")
                break
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            break
    return None
