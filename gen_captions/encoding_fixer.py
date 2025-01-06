"""Fix encoding issues in text files.

This script will scan all text files in the caption and config
directories.
"""
import os
from logging import Logger


def fix_encoding_issues(
    caption_dir,
    config_dir,
    logger: Logger,
):
    """Fix encoding issues in text files."""
    # Build full paths
    encodings = ["utf-8", "latin1", "cp1252"]
    scan_dirs = [caption_dir, config_dir]

    def process_file(file_path, encodings):
        for encoding in encodings:
            logger.info(
                "Scanning file: %s with encoding %s...",
                file_path,
                encoding,
            )
            try:
                with open(file_path, encoding=encoding) as wf:
                    text = wf.read()
                # Write it back in utf-8 to fix encoding issues
                if encoding != "utf-8":
                    text = text.encode("utf-8", "ignore").decode("utf-8")
                    logger.info(
                        "Converting to UTF-8 from %s...",
                        encoding,
                    )
                with open(file_path, "w", encoding="utf-8") as wf:
                    wf.write(text)
                break
            except UnicodeDecodeError as ude:
                logger.error(
                    "Error reading file: %s in %s. Error: %s",
                    file_path,
                    encoding,
                    ude,
                )
                continue

    for scan_dir in scan_dirs:
        for root, _, files in os.walk(scan_dir):
            for file in files:
                if file.endswith((".txt", ".yml", ".yaml")):
                    file_path = os.path.join(root, file)
                    process_file(file_path, encodings)
