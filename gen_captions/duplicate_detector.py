"""Duplicate image detection using multiple confidence layers."""

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import List

import imagehash
from PIL import Image


class DuplicateDetector:
    """Detect duplicate images using multiple detection layers."""

    # Supported image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    def __init__(self, directory: str, console=None):
        """Initialize detector with target directory.

        Args:
            directory: Directory to scan for duplicates
            console: Rich Console for progress display
        """
        self.directory = Path(directory)
        self.image_files: List[Path] = []
        self._file_hashes: dict[Path, str] = {}
        self._perceptual_hashes: dict[Path, imagehash.ImageHash] = {}
        self.console = console

    def scan_images(self) -> List[Path]:
        """Scan directory for image files.

        Returns:
            List of image file paths
        """
        self.image_files = []
        for ext in self.IMAGE_EXTENSIONS:
            self.image_files.extend(self.directory.glob(f'*{ext}'))
            self.image_files.extend(self.directory.glob(f'*{ext.upper()}'))

        # Remove duplicates and sort
        self.image_files = sorted(set(self.image_files))

        # Clear caches when rescanning
        self._file_hashes.clear()
        self._perceptual_hashes.clear()

        return self.image_files

    def find_exact_duplicates(self) -> List[List[dict]]:
        """Find byte-for-byte identical files using MD5 hashing.

        Returns:
            List of duplicate groups, where each group contains file info dicts
        """
        from rich.progress import track
        hash_groups = defaultdict(list)

        iterator = track(self.image_files, description="Computing hashes", console=self.console) if self.console else self.image_files
        for img_path in iterator:
            try:
                # Compute MD5 hash
                md5_hash = hashlib.md5()
                with open(img_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5_hash.update(chunk)

                file_hash = md5_hash.hexdigest()
                self._file_hashes[img_path] = file_hash

                # Get file info
                file_info = self._get_file_info(img_path)
                hash_groups[file_hash].append(file_info)

            except Exception:
                # Skip files that can't be read
                continue

        # Return only groups with duplicates
        return [group for group in hash_groups.values() if len(group) > 1]

    def find_perceptual_duplicates(self, threshold: int = 0) -> List[List[dict]]:
        """Find perceptually similar images using perceptual hashing.

        Args:
            threshold: Hamming distance threshold (0 = identical, higher = more tolerant)

        Returns:
            List of duplicate groups
        """
        from rich.progress import track
        # Compute perceptual hashes for all images
        if not self._perceptual_hashes:
            iterator = track(self.image_files, description="Computing perceptual hashes", console=self.console) if self.console else self.image_files
            for img_path in iterator:
                try:
                    with Image.open(img_path) as img:
                        phash = imagehash.average_hash(img, hash_size=8)
                        self._perceptual_hashes[img_path] = phash
                except Exception:
                    # Skip corrupted images
                    continue

        # Find duplicates by comparing hashes
        duplicates = []
        processed = set()

        files = list(self._perceptual_hashes.keys())
        for i, file1 in enumerate(files):
            if file1 in processed:
                continue

            hash1 = self._perceptual_hashes[file1]
            group = [file1]

            for file2 in files[i+1:]:
                if file2 in processed:
                    continue

                hash2 = self._perceptual_hashes[file2]
                distance = hash1 - hash2

                if distance <= threshold:
                    group.append(file2)
                    processed.add(file2)

            if len(group) > 1:
                # Convert to file info dicts
                group_info = [self._get_file_info(f) for f in group]
                duplicates.append(group_info)
                processed.add(file1)

        return duplicates

    def _get_file_info(self, path: Path) -> dict:
        """Get file information including dimensions and metadata.

        Args:
            path: Path to image file

        Returns:
            Dictionary with file information
        """
        try:
            with Image.open(path) as img:
                width, height = img.size
                format_name = img.format or 'UNKNOWN'
                exif = img.getexif() if hasattr(img, 'getexif') else None
        except Exception:
            width, height = 0, 0
            format_name = 'UNKNOWN'
            exif = None

        return {
            'path': str(path),
            'name': path.name,
            'size': path.stat().st_size,
            'width': width,
            'height': height,
            'format': format_name,
            'exif': exif is not None,
        }
