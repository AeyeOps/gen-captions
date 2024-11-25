# gen_captions/cli.py

import sys
import os
import argparse
from .logger_config import logger
from .system_info import print_system_info
from .constants import OPENAI_API_KEY
from .encoding_fixer import fix_encoding_issues
from .image_processor import process_images

def config_arg_parser():
    parser = argparse.ArgumentParser(
        description="Caption Generator v1.0.5 - Generate image captions for all images in a folder using OpenAI.")
    parser.add_argument("--fix-encoding", action="store_true", help="Fix encoding issues in text files.")
    parser.add_argument("--image-dir", help="Image directory.", required='--fix-encoding' not in sys.argv)
    parser.add_argument("--caption-dir", help="Captions directory for generated text.", required=True)
    parser.add_argument("--config-dir", help="AI toolkit configuration folder.", required=True)
    return parser

def main():
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
    elif not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set in the environment.")
    else:
        process_images(image_directory, caption_directory)

if __name__ == "__main__":
    main()
