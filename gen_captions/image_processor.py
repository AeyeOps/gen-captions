"""Module processes images in the directory and generates descriptions.

A ThreadPoolExecutor is used to asynchronously process images and
generate
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from logging import Logger

from rich.console import Console

from .config import Config
from .llm_client import get_llm_client
from .utils import prompt_exists


def process_images(
    image_directory,
    caption_directory,
    backend,
    config: Config,
    console: Console,
    logger: Logger,
):
    """Process images in the directory and generate descriptions.

    Descriptions are generated using the specified LLM backend and saved
    to the caption directory.
    """
    logger.info("Starting to process images with LLM backend: %s", backend)
    llm_client = get_llm_client(
        backend, config=config, console=console, logger=logger
    )

    with ThreadPoolExecutor(max_workers=config.THREAD_POOL) as executor:
        futures = []
        for filename in os.listdir(image_directory):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                txt_path = os.path.join(caption_directory, txt_filename)

                if not prompt_exists(txt_path):
                    image_path = os.path.join(image_directory, filename)
                    logger.info(
                        "Submitting %s for processing...", filename
                    )
                    future = executor.submit(
                        partial(
                            llm_client.generate_description, image_path
                        )
                    )
                    futures.append((future, txt_path, filename))
                    time.sleep(1 / config.THROTTLE_SUBMISSION_RATE)
                else:
                    logger.info(
                        "Skipping: %s. Prompt already exists.", filename
                    )

        for future in as_completed([f[0] for f in futures]):
            try:
                description = future.result()
                # Convert to UTF-8 in case of special char issues
                description = description.encode("utf-8", "ignore").decode(
                    "utf-8"
                )
                for f in futures:
                    if f[0] == future:
                        txt_path = f[1]
                        filename = f[2]
                        break
                if description and "[trigger]" in description:
                    with open(txt_path, "w", encoding="utf-8") as txt_file:
                        txt_file.write(description)
                    logger.info("Processed: %s", filename)
                elif description:
                    logger.info(
                        "Rejected content for: %s. No [trigger] found. Prompt: %s",
                        filename,
                        description,
                    )
                else:
                    logger.info(
                        "Rejected content for: %s. No description generated.",
                        filename,
                    )
            except Exception as e:
                logger.error(
                    "Error processing image: %s", e, exc_info=True
                )

    logger.info("Finished processing images.")
