import os
from logging import Logger

from rich.console import Console
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeElapsedColumn)


def fix_encoding_issues(
    caption_dir: str,
    config_dir: str,
    logger: Logger,
    console: Console,  # <-- Add a console parameter for Rich output
):
    """Fix encoding issues in text files in caption_dir and config_dir."""
    encodings = ["utf-8", "latin1", "cp1252"]
    scan_dirs = [caption_dir, config_dir]

    # Gather all .txt/.yml/.yaml files to process
    files_to_scan = []
    for scan_dir in scan_dirs:
        if not os.path.isdir(scan_dir):
            logger.warning(
                "Directory does not exist or is not accessible: %s",
                scan_dir,
            )
            continue
        for root, _, files in os.walk(scan_dir):
            for file in files:
                if file.endswith((".txt", ".yml", ".yaml")):
                    file_path = os.path.join(root, file)
                    files_to_scan.append(file_path)

    # If there are no files to scan, bail out
    if not files_to_scan:
        console.print("[bold green]No files found to fix encoding![/]")
        logger.info(
            "No .txt/.yml/.yaml files found in specified directories."
        )
        return

    console.print(
        f"[cyan]Found [bold]{len(files_to_scan)}[/bold] files to scan.[/]"
    )
    logger.info(
        "Found %d files to scan for potential encoding issues.",
        len(files_to_scan),
    )

    # Single function to process a single file
    def process_file(file_path: str):
        """Try to open file under different encodings, convert to UTF-8 if
        needed."""
        for enc in encodings:
            logger.info(
                "Scanning file: %s with encoding %s...", file_path, enc
            )
            try:
                with open(file_path, encoding=enc) as rf:
                    text = rf.read()
                # If we used an encoding other than utf-8, convert it
                if enc != "utf-8":
                    text = text.encode("utf-8", "ignore").decode("utf-8")
                    logger.info(
                        "Converting %s to UTF-8 from %s...", file_path, enc
                    )
                # Write back in UTF-8
                with open(file_path, "w", encoding="utf-8") as wf:
                    wf.write(text)
                break  # Stop checking other encodings once successful
            except UnicodeDecodeError as ude:
                logger.error(
                    "Error reading file: %s in %s. Error: %s",
                    file_path,
                    enc,
                    ude,
                )
                continue

    # Use a single progress bar for scanning
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(
            "Fixing encoding...", total=len(files_to_scan)
        )

        # Process each file and advance progress bar
        for file_path in files_to_scan:
            process_file(file_path)
            progress.advance(task_id)

    console.print("[bold green]Encoding fix completed for all files![/]")
    logger.info("Finished fixing encoding issues for all files.")
