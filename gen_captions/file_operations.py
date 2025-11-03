"""File operations for moving duplicates."""

import shutil
from pathlib import Path
from typing import List


class FileOperations:
    """Handle file moving operations for deduplication."""

    def __init__(self, directory: str):
        """Initialize with target directory.

        Args:
            directory: Directory containing images
        """
        self.directory = Path(directory)
        self.duplicates_dir = self.directory / "duplicates"

    def ensure_duplicates_dir(self):
        """Create duplicates directory if it doesn't exist."""
        self.duplicates_dir.mkdir(exist_ok=True)

    def move_to_duplicates(self, file_info: dict) -> bool:
        """Move a file and its caption (if exists) to duplicates directory.

        Args:
            file_info: Dictionary with file information

        Returns:
            True if successful, False otherwise
        """
        try:
            src_path = Path(file_info['path'])

            # Determine destination path
            dst_path = self.duplicates_dir / src_path.name

            # Handle name collision
            counter = 1
            while dst_path.exists():
                stem = src_path.stem
                suffix = src_path.suffix
                dst_path = self.duplicates_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            # Move the image file
            shutil.move(str(src_path), str(dst_path))

            # Move caption file if it exists
            caption_src = src_path.with_suffix('.txt')
            if caption_src.exists():
                caption_dst = dst_path.with_suffix('.txt')
                shutil.move(str(caption_src), str(caption_dst))

            return True

        except Exception:
            return False

    def move_duplicates(self, duplicates: List[dict]) -> tuple:
        """Move multiple duplicate files to duplicates directory.

        Args:
            duplicates: List of file info dictionaries to move

        Returns:
            Tuple of (success_count, total_bytes_moved)
        """
        success_count = 0
        total_bytes = 0

        for file_info in duplicates:
            if self.move_to_duplicates(file_info):
                success_count += 1
                total_bytes += file_info['size']

        return success_count, total_bytes
