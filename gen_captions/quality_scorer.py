"""Quality scoring system for selecting best image from duplicates."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FileInfo = Dict[str, Any]


class QualityScorer:
    """Score image quality based on multiple factors."""

    # Patterns that indicate lower quality filenames
    BAD_FILENAME_PATTERNS = [
        "copy",
        "duplicate",
        "temp",
        "thumb",
        "backup",
        "(1)",
        "(2)",
    ]

    # Format quality preferences
    FORMAT_SCORES = {
        "PNG": 10,
        "WEBP": 8,
        "JPG": 5,
        "JPEG": 5,
        "GIF": 3,
        "BMP": 2,
    }

    def __init__(self, directory: str):
        """Initialize scorer with target directory.

        Args:
            directory: Directory containing images
        """
        self.directory = Path(directory)

    def score_file(self, file_info: FileInfo) -> float:
        """Calculate comprehensive quality score for an image.

        Args:
            file_info: Dictionary with file information

        Returns:
            Quality score (higher is better)
        """
        score = 0.0
        path = Path(str(file_info.get("path", "")))
        width = int(file_info.get("width", 0))
        height = int(file_info.get("height", 0))
        size_bytes = int(file_info.get("size", 0))

        # HIGHEST PRIORITY: Has caption file (worth 1000 points)
        if self.has_caption_file(path):
            score += 1000

        # Resolution quality (up to 30 points)
        pixels = width * height
        megapixels = pixels / 1_000_000
        score += min(megapixels * 3, 30)

        # Compression quality - bytes per pixel (up to 20 points)
        if pixels > 0:
            bytes_per_pixel = size_bytes / pixels
            if bytes_per_pixel > 0.5:
                score += 20  # High quality
            elif bytes_per_pixel > 0.3:
                score += 15  # Medium-high quality
            elif bytes_per_pixel > 0.1:
                score += 10  # Medium quality
            else:
                score += 5  # Heavily compressed

        # Format preference (up to 10 points)
        format_upper = str(file_info.get("format", "")).upper()
        score += self.FORMAT_SCORES.get(format_upper, 0)

        # Filename quality (up to 10 points)
        filename_lower = path.stem.lower()
        if not any(
            bad in filename_lower
            for bad in self.BAD_FILENAME_PATTERNS
        ):
            score += 10

        # Has EXIF data (5 points)
        if file_info.get("exif"):
            score += 5

        return score

    def recommend_keeper(
        self, group: List[FileInfo]
    ) -> Tuple[Optional[FileInfo], str]:
        """Recommend which file to keep from a duplicate group.

        Args:
            group: List of file info dictionaries

        Returns:
            Tuple of (best file info, reason string)
        """
        if not group:
            return None, "Empty group"

        if len(group) == 1:
            return group[0], "Only file in group"

        # Score each file
        scored = [
            (file_info, self.score_file(file_info))
            for file_info in group
        ]

        # Find best file
        best_file, best_score = max(scored, key=lambda x: x[1])

        # Generate reason
        reasons = []
        path = Path(best_file["path"])

        if self.has_caption_file(path):
            reasons.append("has caption")

        if best_file["size"] == max(f["size"] for f in group):
            reasons.append("largest file")

        if best_file["width"] * best_file["height"] == max(
            f["width"] * f["height"] for f in group
        ):
            reasons.append("highest resolution")

        if best_file["format"].upper() == "PNG":
            reasons.append("lossless format")

        if not reasons:
            reasons.append("best quality score")

        reason = ", ".join(reasons)

        return best_file, reason

    def has_caption_file(self, image_path: Path) -> bool:
        """Check if a caption file exists for this image.

        Args:
            image_path: Path to image file

        Returns:
            True if caption file exists
        """
        caption_path = image_path.with_suffix(".txt")
        return caption_path.exists()

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
