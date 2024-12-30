# gen_captions/image_processor.py

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from .logger_config import logger
from .constants import THREAD_POOL, THROTTLE_SUBMISSION_RATE
from .utils import prompt_exists
from .openai_api import generate_description

def process_images(image_directory, caption_directory):
    """Process images in the directory and generate descriptions asynchronously."""
    logger.info("Starting to process images...")
    with ThreadPoolExecutor(max_workers=THREAD_POOL) as executor:
        futures = []
        for filename in os.listdir(image_directory):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                txt_path = os.path.join(caption_directory, txt_filename)

                if not prompt_exists(txt_path):
                    image_path = os.path.join(image_directory, filename)
                    logger.info(f"Submitting {filename} for processing...")
                    future = executor.submit(partial(generate_description, image_path))
                    futures.append((future, txt_path, filename))
                    time.sleep(1 / THROTTLE_SUBMISSION_RATE)  # Add delay between task submissions
                else:
                    logger.info(f"Skipping: {filename}. Prompt already exists.")

        # Use as_completed to handle futures as they complete
        for future in as_completed([f[0] for f in futures]):
            try:
                description = future.result()
                # Find the corresponding txt_path and filename
                description = description.encode('utf-8', 'ignore').decode('utf-8')
                for f in futures:
                    if f[0] == future:
                        txt_path = f[1]
                        filename = f[2]
                        break
                if description:
                    if "[trigger]" in description:
                        with open(txt_path, "w", encoding="utf-8") as txt_file:
                            txt_file.write(description)
                        logger.info(f"Processed: {filename}")
                    else:
                        logger.info(f"Rejected content for: {filename}. No [trigger] found.")
            except Exception as e:
                logger.error(f"Error processing image: {e}")
    logger.info("Finished processing images.")
