"""LLM-driven removal workflow for dataset filtering."""

from __future__ import annotations

import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich import progress as rich_progress
from rich.console import Console

from .config import Config
from .llm_client import get_llm_client

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def remove_mismatched_images(
    image_directory: str,
    backend: str,
    config: Config,
    console: Console,
    logger: Logger,
    desired_gender: Optional[str],
    require_solo: Optional[bool],
) -> Dict[str, Any]:
    """Analyze images and move mismatches into an isolated directory."""

    llm_client = get_llm_client(
        backend, config=config, console=console, logger=logger
    )

    images = _list_image_files(image_directory)
    if not images:
        console.print(
            "[yellow]No JPG/JPEG/PNG/WEBP/BMP files found to analyze.[/]"
        )
        removal_dir = Path(image_directory) / "removed"
        removal_dir.mkdir(parents=True, exist_ok=True)
        return {
            "processed": 0,
            "removed": 0,
            "results": [],
            "destination": str(removal_dir),
        }

    console.print(
        f"[bold green]Preparing to analyze {len(images)} image(s) for removal.[/]"
    )
    logger.info(
        "Analyzing %d images for removal filters (desired_gender=%s, require_solo=%s)",
        len(images),
        desired_gender,
        require_solo,
    )

    removal_dir = Path(image_directory) / "removed"
    removal_dir.mkdir(parents=True, exist_ok=True)

    future_map: Dict[Any, Path] = {}
    results: List[Dict[str, Any]] = []
    removed_count = 0
    processed_count = 0
    thresholds = config.get_removal_thresholds()

    with ThreadPoolExecutor(
        max_workers=config.THREAD_POOL
    ) as executor:
        submission_delay = 1 / config.THROTTLE_SUBMISSION_RATE
        total_images = len(images)
        for idx, image_path in enumerate(images, start=1):
            future = executor.submit(
                partial(
                    llm_client.generate_removal_metadata,
                    str(image_path),
                )
            )
            future_map[future] = image_path
            time.sleep(submission_delay)
            if idx == 1 or idx == total_images or idx % 25 == 0:
                console.print(
                    f"[dim]Queued {idx}/{total_images} image(s) for analysis...[/]"
                )

        console.print(
            f"[dim]All {total_images} image(s) queued. Awaiting LLM decisions...[/]"
        )

        with rich_progress.Progress(
            rich_progress.SpinnerColumn(),
            rich_progress.BarColumn(),
            rich_progress.TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%"
            ),
            rich_progress.TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(
                "Analyzing images...", total=total_images
            )

            for future in as_completed(future_map):
                progress.advance(task_id)
                image_path = future_map[future]
                try:
                    analysis = future.result()
                except (
                    Exception
                ) as exc:  # pragma: no cover - defensive
                    logger.error(
                        "Removal analysis failed for %s: %s",
                        image_path,
                        exc,
                    )
                    analysis = {}

                processed_count += 1
                logger.debug(
                    "[Removal] raw metadata for %s: %s",
                    image_path.name,
                    analysis,
                )

                decision, reasons = _evaluate_removal_decision(
                    analysis,
                    desired_gender,
                    require_solo,
                    thresholds,
                )

                destination = None
                action = "kept"
                if decision:
                    removed_count += 1
                    destination = str(
                        _move_to_removed(image_path, removal_dir)
                    )
                    action = "moved"

                entry = {
                    "image": str(image_path),
                    "analysis": analysis,
                    "should_remove": bool(decision),
                    "reasons": reasons,
                    "action": action,
                    "destination": destination,
                }
                results.append(entry)
                reason_text = "; ".join(reasons) if reasons else "meets requirements"
                stats_text = (
                    f"solo={analysis.get('is_solo_p', 0.0):.2f} "
                    f"women={analysis.get('is_woman_p', 0.0):.2f} "
                    f"men={analysis.get('is_man_p', 0.0):.2f}"
                )
                dest_text = f" -> {destination}" if destination else ""
                console.print(
                    (
                        f"[bold cyan]{processed_count}/{total_images}[/] "
                        f"{image_path.name} [{action.upper()}] {stats_text} "
                        f"reason={reason_text}{dest_text}"
                    )
                )
                logger.info(
                    (
                        "Removal analysis: %s/%s %s -> %s (removed=%s) "
                        "reasons=%s probabilities=%s"
                    ),
                    processed_count,
                    total_images,
                    image_path.name,
                    action,
                    bool(decision),
                    reasons or ["meets requirements"],
                    {
                        "is_solo_p": analysis.get("is_solo_p"),
                        "is_woman_p": analysis.get("is_woman_p"),
                        "is_man_p": analysis.get("is_man_p"),
                        "thought": analysis.get("thought"),
                    },
                )

    console.print(
        f"[bold green]Removal analysis complete. Moved {removed_count} file(s) into '{removal_dir.name}'."  # noqa: E501
    )
    logger.info(
        "Removal analysis complete. Removed %d of %d images",
        removed_count,
        len(images),
    )

    return {
        "processed": len(images),
        "removed": removed_count,
        "results": results,
        "destination": str(removal_dir),
    }


def _list_image_files(directory: str) -> List[Path]:
    """Return sorted image paths inside the directory."""
    root = Path(directory)
    if not root.exists():
        return []

    files = [
        path
        for path in sorted(root.iterdir())
        if path.suffix.lower() in SUPPORTED_EXTENSIONS
        and path.is_file()
    ]
    return files


def _move_to_removed(
    image_path: Path,
    removal_dir: Path,
) -> Path:
    """Move image (and caption file) into the removal directory."""
    removal_dir.mkdir(parents=True, exist_ok=True)
    destination = removal_dir / image_path.name
    counter = 1
    while destination.exists():
        destination = (
            removal_dir
            / f"{image_path.stem}_{counter}{image_path.suffix}"
        )
        counter += 1

    shutil.move(str(image_path), str(destination))

    caption_src = image_path.with_suffix(".txt")
    if caption_src.exists():
        caption_dst = destination.with_suffix(".txt")
        shutil.move(str(caption_src), str(caption_dst))

    return destination


def _evaluate_removal_decision(
    analysis: Dict[str, Any],
    desired_gender: Optional[str],
    require_solo: Optional[bool],
    thresholds: Dict[str, float],
) -> Tuple[bool, List[str]]:
    """Determine whether an image should be removed."""
    reasons: List[str] = []
    should_remove = False

    if desired_gender:
        gender_key = (
            "is_woman_p"
            if desired_gender == "women"
            else "is_man_p"
        )
        gender_prob = _safe_float(analysis.get(gender_key, 0.0))
        gender_threshold = thresholds.get(gender_key, 0.9)
        if gender_prob < gender_threshold:
            should_remove = True
            reasons.append(
                (
                    f"Expected {desired_gender} probability >= {gender_threshold:.2f}, "
                    f"got {gender_prob:.2f}"
                )
            )

    if require_solo is not None:
        solo_prob = _safe_float(analysis.get("is_solo_p", 0.0))
        solo_threshold = thresholds.get("is_solo_p", 0.9)
        if require_solo and solo_prob < solo_threshold:
            should_remove = True
            reasons.append(
                f"Expected solo probability >= {solo_threshold:.2f}, got {solo_prob:.2f}"
            )
        elif not require_solo:
            group_prob = 1 - solo_prob
            group_threshold = 1 - solo_threshold
            if group_prob < group_threshold:
                should_remove = True
                reasons.append(
                    (
                        f"Expected group probability >= {group_threshold:.2f}, "
                        f"got {group_prob:.2f}"
                    )
                )

    return should_remove, reasons


def _safe_float(value: Any) -> float:
    """Convert arbitrary value into float with sensible default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
