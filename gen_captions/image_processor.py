import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from logging import Logger

from rich.console import Console
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeElapsedColumn)

from .config import Config
from .llm_client import get_llm_client
from .utils import prompt_exists


def process_images(
    image_directory,
    caption_directory,
    backend,
    config: Config,
    console: Console,
    logger: Logger,
):
    """Process images in the directory and generate descriptions.

    Descriptions are generated using the specified LLM backend and saved
    to the caption directory.
    """
    # Provide a visible console message to indicate start
    console.print(
        f"[bold green]Starting to process images with LLM backend: {backend}[/]"
    )
    logger.info("Starting to process images with LLM backend: %s", backend)

    llm_client = get_llm_client(
        backend, config=config, console=console, logger=logger
    )

    # Gather list of images that actually need processing
    console.print(
        "[bold cyan]Scanning directory for images to process...[/]"
    )
    images_to_process = []
    skipped_count = 0

    for filename in os.listdir(image_directory):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(caption_directory, txt_filename)
            if not prompt_exists(txt_path):
                images_to_process.append((filename, txt_path))
            else:
                skipped_count += 1

    # Print skip info (just a summary, not per-file spam)
    if skipped_count > 0:
        console.print(
            f"[bold yellow]Skipped {skipped_count} image(s) that already have prompts.[/]"
        )
        logger.info(
            "Skipped %d images that already have prompts.", skipped_count
        )

    # If nothing to do, bail out early
    if not images_to_process:
        console.print("[bold green]No new images to process. All done![/]")
        logger.info("No new images to process. Finished.")
        return

    console.print(
        f"[bold cyan]Found {len(images_to_process)} image(s) that need processing.[/]"
    )

    # Simple console print instead of creating a second live display
    console.print(
        "[bold green]Submitting tasks to ThreadPoolExecutor...[/]"
    )

    futures = []
    with ThreadPoolExecutor(max_workers=config.THREAD_POOL) as executor:
        # Submit tasks
        for filename, txt_path in images_to_process:
            image_path = os.path.join(image_directory, filename)
            logger.info("Submitting %s for processing...", filename)
            future = executor.submit(
                partial(llm_client.generate_description, image_path)
            )
            futures.append((future, txt_path, filename))

            # Throttle submission rate
            time.sleep(1 / config.THROTTLE_SUBMISSION_RATE)

        # Use a single Progress bar (only one live display)
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(
                "Generating descriptions...", total=len(futures)
            )

            # Process completed tasks
            for future in as_completed([f[0] for f in futures]):
                progress.advance(task_id)
                try:
                    description = future.result()
                    # Convert to UTF-8 in case of special char issues
                    description = description.encode(
                        "utf-8", "ignore"
                    ).decode("utf-8")

                    # Find the relevant file info
                    for f in futures:
                        if f[0] == future:
                            txt_path = f[1]
                            filename = f[2]
                            break

                    # Check result for "[trigger]"
                    if description and "[trigger]" in description:
                        with open(
                            txt_path, "w", encoding="utf-8"
                        ) as txt_file:
                            txt_file.write(description)
                        logger.info("Processed: %s", filename)
                    elif description:
                        logger.info(
                            "Rejected content for: %s. No [trigger] found. Prompt: %s",
                            filename,
                            description,
                        )
                        console.print(
                            f"[bold yellow]Rejected content for: {filename}. No trigger found.[/]"
                        )
                    else:
                        logger.info(
                            "Rejected content for: %s. No description generated.",
                            filename,
                        )
                        console.print(
                            f"[bold yellow]Rejected content for: {filename}. No description generated.[/]"
                        )
                except Exception as e:
                    logger.error(
                        "Error processing image: %s", e, exc_info=True
                    )
                    console.print(
                        f"[bold red]Error processing image: {e}[/]"
                    )
    # Provide a final console message
    console.print("[bold green]Finished processing images.[/]")
    logger.info("Finished processing images.")
