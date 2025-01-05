import os
from .logger_config import logger


def fix_encoding_issues(caption_dir, config_dir):
    """Fix encoding issues in text files."""
    # Build full paths
    encodings = ["utf-8", "latin1", "cp1252"]
    scan_dirs = [caption_dir, config_dir]

    for dir in scan_dirs:
        for root, _, files in os.walk(dir):
            for file in files:
                if file.endswith((".txt", ".yml", ".yaml")):
                    file_path = os.path.join(root, file)
                    for encoding in encodings:
                        logger.info(
                            f"Scanning file: {file_path} with encoding {encoding}..."
                        )
                        try:
                            with open(file_path, "r", encoding=encoding) as f:
                                text = f.read()
                            # Write it back in utf-8 to fix encoding issues
                            if encoding != "utf-8":
                                text = text.encode("utf-8", "ignore").decode("utf-8")
                                logger.info(f"Converting to UTF-8 from {encoding}...")
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(text)
                            break
                        except UnicodeDecodeError as e:
                            logger.error(
                                f"Error reading file: {file_path} in {encoding}. Error: {e}"
                            )
                            continue
