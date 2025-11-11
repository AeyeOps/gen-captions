"""Interactive duplicate detection and cleanup command."""

import sys
import termios
import tty
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional, Union

import typer
from rich.console import Console
from rich.progress import track

from .duplicate_detector import DuplicateDetector
from .file_operations import FileOperations
from .quality_scorer import QualityScorer

FileInfo = Dict[str, Any]


class DedupeProcessor:
    """Process duplicate detection and cleanup with user interaction."""

    def __init__(
        self,
        directory: str,
        yolo_mode: bool = False,
        console: Optional[Console] = None,
    ):
        """Initialize the dedupe processor.

        Args:
            directory: Directory to deduplicate
            yolo_mode: If True, auto-execute all recommendations
            console: Rich console for output
        """
        self.directory = Path(directory)
        self.yolo_mode = yolo_mode
        self.console = console or Console()

        self.detector = DuplicateDetector(
            str(directory), console=self.console
        )
        self.scorer = QualityScorer(str(directory))
        self.file_ops = FileOperations(str(directory))

        # Detection layers with thresholds
        self.layers = [
            ("EXACT", "Byte-for-byte identical", 100, "exact"),
            ("IDENTICAL", "Visually identical", 95, 0),
            ("NEAR-IDENTICAL", "Tiny variations", 85, 2),
            ("VERY_SIMILAR", "Different processing", 70, 2),
            ("SIMILAR", "Variants/burst mode", 50, 2),
        ]

        # Statistics
        self.kept = 0
        self.moved = 0
        self.space_saved = 0
        self.by_layer: DefaultDict[str, int] = defaultdict(int)

    def run(self):
        """Main execution flow."""
        mode_str = (
            "[YOLO MODE]" if self.yolo_mode else "[INTERACTIVE]"
        )
        self.console.print(f"\nDuplicate Detection {mode_str}")
        self.console.print(f"Directory: {self.directory}\n")

        # Create duplicates directory
        self.file_ops.ensure_duplicates_dir()

        # Scan images
        self.console.print("Scanning images...", end=" ")
        images = self.detector.scan_images()
        self.console.print(f"found {len(images)} images\n")

        if not images:
            self.console.print(
                "[yellow]No images found[/yellow]"
            )
            return

        # Process each layer
        for name, desc, confidence, threshold in self.layers:
            skip_layer = self.process_layer(
                name, desc, confidence, threshold
            )
            if skip_layer:
                break

        # Show final summary
        self.show_summary()

    def process_layer(
        self,
        name: str,
        desc: str,
        confidence: int,
        threshold: Union[str, int],
    ) -> bool:
        """Process a single detection layer.

        Args:
            name: Layer name
            desc: Layer description
            confidence: Confidence percentage
            threshold: Detection threshold ('exact' or int)

        Returns:
            True if user wants to exit, False otherwise
        """
        width = (
            self.console.width
            if hasattr(self.console, "width")
            else 70
        )
        self.console.print("─" * width, style="dim")
        self.console.print(
            f"Layer: {name} ({confidence}% confidence match)"
        )

        # Explain what this layer does
        explanations = {
            "EXACT": (
                "Finds files that are 100% identical (same bytes). "
                "These are safe to remove."
            ),
            "IDENTICAL": (
                "Finds images that look identical but may have different "
                "metadata. Very safe."
            ),
            "NEAR-IDENTICAL": (
                "Finds images with tiny differences (small crops, "
                "watermarks). Low risk."
            ),
            "VERY_SIMILAR": (
                "Finds same image with different processing (filters, "
                "resolution). Medium risk."
            ),
            "SIMILAR": (
                "Finds related images (burst photos, similar shots). "
                "Higher risk - review carefully."
            ),
        }

        risk_levels = {
            "EXACT": "SAFE",
            "IDENTICAL": "SAFE",
            "NEAR-IDENTICAL": "LOW RISK",
            "VERY_SIMILAR": "MEDIUM RISK",
            "SIMILAR": "HIGHER RISK",
        }

        self.console.print(
            f"What this finds: {explanations.get(name, desc)}"
        )
        self.console.print(
            f"Risk level: {risk_levels.get(name, 'UNKNOWN')}\n"
        )

        # Rescan to exclude moved files
        self.detector.scan_images()

        # Find duplicates
        if threshold == "exact":
            groups = self.detector.find_exact_duplicates()
        else:
            threshold_value = int(threshold)
            groups = self.detector.find_perceptual_duplicates(
                threshold_value
            )

        if not groups:
            self.console.print("No duplicates found\n")
            return False

        # Show summary of what was found
        total_files = sum(len(g) for g in groups)
        files_to_move = total_files - len(groups)
        self.console.print(
            f"Found {len(groups)} duplicate groups ({files_to_move} files to move)\n"
        )

        # In YOLO mode, process all automatically
        if self.yolo_mode:
            return self._process_all_groups(groups, name)

        # Interactive: show preview and get ONE decision for entire layer
        return self._process_layer_interactive(groups, name)

    def _process_layer_interactive(
        self, groups: List[List[FileInfo]], layer_name: str
    ) -> bool:
        """Show layer summary and get single decision."""
        from rich.table import Table

        # Show ALL groups in a table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Keep", style="green")
        table.add_column("Duplicates to Move", style="dim")

        for group in groups:
            keep_file, reason = self.scorer.recommend_keeper(
                group
            )
            if keep_file is None:
                continue
            duplicates = [
                f["name"] for f in group if f != keep_file
            ]
            table.add_row(
                keep_file["name"], ", ".join(duplicates)
            )

        self.console.print(
            f"\nFound {len(groups)} duplicate groups:\n"
        )
        self.console.print(table)
        self.console.print()

        # Single prompt for entire layer
        self.console.print(
            "\n      (c)ontinue - Process ALL groups in this layer"
        )
        self.console.print(
            "      (s)kip - Skip this entire layer"
        )
        self.console.print(
            "      e(x)it - Stop and show summary",
            markup=False,
            highlight=False,
        )
        choice = self._getch().lower()

        # Ignore Enter key
        if choice in ("\n", "\r", ""):
            self.console.print("      Please press c, s, or x\n")
            return False

        self.console.print(choice)

        if choice == "c":
            return self._process_all_groups(groups, layer_name)
        elif choice == "s":
            self.console.print("      Skipped layer\n")
            return False
        elif choice == "x":
            self.console.print("\n      Exiting...\n")
            return True
        else:
            self.console.print(
                "      Invalid choice, skipping layer\n"
            )
            return False

    def _process_all_groups(
        self, groups: List[List[FileInfo]], layer_name: str
    ) -> bool:
        """Process all groups in a layer."""
        for group in track(
            groups, description=f"Processing {layer_name}"
        ):
            keep_file, reason = self.scorer.recommend_keeper(
                group
            )
            if keep_file is None:
                continue
            duplicates = [f for f in group if f != keep_file]
            self.execute_move(keep_file, duplicates, layer_name)

        # Layer summary
        if self.by_layer[layer_name] > 0:
            moved = self.by_layer[layer_name]
            self.console.print(
                f"Layer complete: moved {moved} duplicates\n"
            )

        return False

    def process_group(
        self,
        group: List[FileInfo],
        group_num: int,
        total: int,
        layer_name: str,
        auto_mode: bool,
    ):
        """Process a single duplicate group.

        Args:
            group: List of file info dicts
            group_num: Current group number
            total: Total groups in layer
            layer_name: Name of current layer
            auto_mode: If True, auto-accept recommendations

        Returns:
            User action: 'continue', 'skip_layer', 'auto', or 'exit'
        """
        self.console.print(
            f"  [{group_num}/{total}] {len(group)} files are duplicates"
        )

        # Add user-friendly explanation
        self.console.print(
            "\n      These files are the same image. We'll keep one and move the"
        )
        self.console.print(
            "      others to duplicates/ folder so you can review or delete them later."
        )

        # Show files
        self.console.print()
        for file_info in sorted(
            group, key=lambda x: x["size"], reverse=True
        ):
            caption_marker = (
                "[HAS CAPTION]"
                if self.scorer.has_caption_file(
                    Path(file_info["path"])
                )
                else ""
            )
            size_str = self.scorer.format_size(file_info["size"])
            self.console.print(
                f"      {file_info['name']:<35} {size_str:>8} "
                f"{file_info['width']}x{file_info['height']} {caption_marker}"
            )

        # Get recommendation
        keep_file, reason = self.scorer.recommend_keeper(group)
        if keep_file is None:
            self.console.print(
                "      Unable to determine keeper, skipping group"
            )
            return "continue"
        duplicates = [f for f in group if f != keep_file]

        self.console.print(
            f"\n      We recommend keeping: {keep_file['name']}"
        )
        self.console.print(f"      Because: {reason}")
        self.console.print(
            f"      This will move {len(duplicates)} duplicate(s) to duplicates/ folder."
        )

        # Execute or prompt
        if self.yolo_mode or auto_mode:
            self.execute_move(keep_file, duplicates, layer_name)
            self.console.print()
            return "continue"
        else:
            return self.prompt_user(
                keep_file, duplicates, group, layer_name
            )

    def prompt_user(
        self,
        keep_file: FileInfo,
        duplicates: List[FileInfo],
        group: List[FileInfo],
        layer_name: str,
    ) -> str:
        """Prompt user for action.

        Args:
            keep_file: Recommended file to keep
            duplicates: Files to move
            group: All files in group
            layer_name: Current layer name

        Returns:
            User action
        """
        self.console.print("\n      (c)ontinue (s)kip e(x)it")
        choice = self._getch().lower()
        self.console.print(choice)

        if choice == "" or choice == "c":
            self.execute_move(keep_file, duplicates, layer_name)
            self.console.print()
            return "continue"

        elif choice == "s":
            self.console.print("      Skipping rest of layer\n")
            return "skip_layer"

        elif choice == "x":
            self.console.print("\n      Exiting...\n")
            return "exit"

        else:
            self.console.print(
                "      Invalid choice, continuing...\n"
            )
            return "continue"

    def execute_move(
        self,
        keep_file: FileInfo,
        duplicates: List[FileInfo],
        layer_name: str,
    ):
        """Move duplicate files to duplicates directory.

        Args:
            keep_file: File to keep
            duplicates: Files to move
            layer_name: Current layer name
        """
        for dup in duplicates:
            if self.file_ops.move_to_duplicates(dup):
                self.console.print(
                    f"      -> {dup['name']} moved to duplicates/"
                )
                self.moved += 1
                self.space_saved += dup["size"]
                self.by_layer[layer_name] += 1

        self.kept += 1

    def _getch(self):
        """Get single character input without Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(
                fd, termios.TCSADRAIN, old_settings
            )
        return ch

    def show_summary(self):
        """Display final summary."""
        width = (
            self.console.width
            if hasattr(self.console, "width")
            else 70
        )
        self.console.print("═" * width, style="dim")
        self.console.print("DEDUPLICATION COMPLETE")
        self.console.print("═" * width, style="dim")
        self.console.print()

        self.console.print(f"  Files kept:        {self.kept}")
        self.console.print(f"  Files moved:       {self.moved}")
        space_str = self.scorer.format_size(self.space_saved)
        self.console.print(f"  Space saved:       {space_str}")

        if self.by_layer:
            self.console.print("\n  By Layer:")
            for layer, count in self.by_layer.items():
                if count > 0:
                    self.console.print(
                        f"    {layer:<15} {count} duplicates"
                    )

        self.console.print(f"\n  Deduped:    {self.directory}/")
        self.console.print(
            f"  Duplicates: {self.file_ops.duplicates_dir}/"
        )
        self.console.print()


def dedupe_command(
    image_dir: str = typer.Option(
        ".",
        "--image-dir",
        help="Directory containing images to deduplicate (default: current directory)",
    ),
    yolo: bool = typer.Option(
        False,
        "--yolo",
        help="Auto-execute all recommendations without prompting",
    ),
    console: Optional[Console] = None,
):
    """Interactive duplicate image detection and cleanup.

    Finds and removes duplicate images using multiple detection layers,
    from exact byte-for-byte matches to perceptually similar images.
    """
    processor = DedupeProcessor(
        image_dir, yolo_mode=yolo, console=console
    )
    processor.run()
