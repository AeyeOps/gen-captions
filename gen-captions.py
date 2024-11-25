import os
import sys
from openai import OpenAI
from dotenv import load_dotenv
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import logging
import requests
import time
import platform
from argparse import ArgumentParser

# Load environment variables
load_dotenv()
load_dotenv(".env.local")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
THREAD_POOL = int(os.getenv("GETCAP_THREAD_POOL", 10))
THROTTLE_RETRIES = int(os.getenv("GETCAP_THROTTLE_RETRIES", 10))
THROTTLE_BACKOFF_FACTOR = float(os.getenv("GETCAP_THROTTLE_BACKOFF_FACTOR", 2))
LOG_LEVEL = os.getenv("GETCAP_LOG_LEVEL", "INFO")
THROTTLE_SUBMISSION_RATE = float(os.getenv("GETCAP_THROTTLE_SUBMISSION_RATE", 1))

# Configure logging
# Add a padded thread id to the log output for easier debugging
logging.basicConfig(
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger(__name__)

def print_system_info():
    """Print system information and environment variable settings."""
    print("\r\n" * 2)
    logger.info("System Information:")
    logger.info(f"Platform: {platform.system()}")
    logger.info(f"Platform Version: {platform.version()}")
    logger.info(f"Platform Release: {platform.release()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Python Version: {platform.python_version()}")

    logger.info("Environment Variable Settings:")
    for key, value in os.environ.items():
        if key.startswith("GETCAP_"):
            logger.info(f"{key}: {value}")
    print("\r\n" * 2)

def prompt_exists(text_file):
    """Check if the prompt file already exists and is not empty."""
    return os.path.exists(text_file) and os.stat(text_file).st_size > 0


def encode_image(image_path):
    """Encode the image to base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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
                                    Do not capitalize the name regardless of where you place it in the setence it should always be lowercase [trigger].
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


def process_images(image_directory, caption_directory):
    """Process images in the directory and generate descriptions asynchronously."""
    logger.info("Starting to process images...")
    with ThreadPoolExecutor(max_workers=THREAD_POOL) as executor:
        futures = []
        for filename in os.listdir(image_directory):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                txt_filename = filename.rsplit(".", 1)[0] + ".txt"
                txt_path = os.path.join(caption_directory, txt_filename)

                if not prompt_exists(txt_path):
                    image_path = os.path.join(image_directory, filename)
                    logger.info(f"Submitting {filename} for processing...")
                    future = executor.submit(partial(generate_description, image_path))
                    futures.append((future, txt_path, filename))
                    time.sleep(1/THROTTLE_SUBMISSION_RATE)  # Add delay between task submissions
                else:
                    logger.info(f"Skipping: {filename}. Prompt already exists.")

        # Use as_completed to handle futures as they complete
        for future in as_completed([f[0] for f in futures]):
            try:
                description = future.result()
                # Find the corresponding txt_path and filename
                # encode to utf-8
                description = description.encode('utf-8', 'ignore').decode('utf-8')
                for f in futures:
                    if f[0] == future:
                        txt_path = f[1]
                        filename = f[2]
                        break
                if description:
                    with open(txt_path, "w", encoding="utf-8" ) as txt_file:
                        txt_file.write(description)
                    logger.info(f"Processed: {filename}")
            except Exception as e:
                logger.error(f"Error processing image: {e}")
    logger.info("Finished processing images.")

def fix_encoding_issues(image_dir, config_dir):
    # If we are passing a parameter called --fix-encoding then:
    # Walk every text file and scan it for 0x92 bytes or single quotation marks.
    # Walk the config file as well and scan it for 0x92 bytes or single quotation marks.
    # If we find any, open the file in utf-8 and write it back in utf-8
    # Print a message to track the actions and then exit the program

    # Build full paths
    image_dir = os.path.abspath(image_dir)
    config_dir = os.path.abspath(config_dir)
    encodings = ["utf-8", "latin1", "cp1252"]
    scan_dirs = [image_dir, config_dir]

    for dir in scan_dirs:
        for root, _, files in os.walk(dir):
            for file in files:
                if file.endswith(".txt") or file.endswith(".yml") or file.endswith(".yaml"):
                    file_path = os.path.join(root, file)
                    encodings = ["utf-8", "latin1", "cp1252"]
                    for encoding in encodings:
                        logger.info(f"Scanning file: {file_path} with encoding {encoding}...")
                        with open(file_path, "r", encoding=encoding) as f:
                            try:
                                text = f.read()
                                # write it back in utf-8 to fix encoding issues
                                # convert it to utf-8 if it is not already
                                if encoding != "utf-8":
                                    text = text.encode('utf-8', 'ignore').decode('utf-8')
                                    logger.info(f"Converting to utf8 from {encoding}...")
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(text)
                                break
                            except UnicodeDecodeError as e:
                                logger.error(f"Error reading file: {file_path} in {encoding}. Error: {e}")
                                continue
def config_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Caption Generator v1.0.5 - Generate image captions for all images in a folder using OpenAI.")
    parser.add_argument("--fix-encoding", action="store_true", help="Fix encoding issues in text files.")
    # the following are required only if --fix-encoding is not set
    parser.add_argument("--image-dir", help="Image directory.", required='--fix-encoding' not in sys.argv)
    parser.add_argument("--caption-dir", help="Captions directory for generated text.", required=True)
    parser.add_argument("--config-dir", help="ai-toolkit configuration folder.", required=True)
    return parser


if __name__ == "__main__":

    parser = config_arg_parser()
    print("\r\n" * 1)    
    print(parser.description)
    print("\r\n" * 1)
    args = parser.parse_args()
    print("\r\n" * 2)        
    print_system_info()
    print("\r\n" * 2)
    
    
    # Get the full path of the image directory
    image_directory = os.path.abspath(args.image_dir) if args.image_dir else None
    caption_directory = os.path.abspath(args.caption_dir) if args.caption_dir else None
    config_directory = os.path.abspath(args.config_dir) if args.config_dir else None
    
    if args.fix_encoding:
        logger.info("Fixing encoding issues in text files...")  
        fix_encoding_issues(caption_directory, config_directory)
        logger.info("Finished fixing encoding issues.")
    elif not OpenAI.api_key:
        logger.error("OPENAI_API_KEY is not set in the environment.")
    else:
        process_images(image_directory, caption_directory)

