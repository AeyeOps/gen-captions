"""Helpers for rendering diagnostic tables in the CLI."""

from __future__ import annotations

import os
import platform
from logging import Logger
from typing import Iterable, Tuple

from rich.console import Console
from rich.table import Table

_TRACKED_PREFIXES = ("OPENAI_", "GROK_", "GETCAP_", "GEN_CAPTIONS_")


def print_system_info(
    console: Console,
    logger: Logger,
    config_snapshot: Iterable[Tuple[str, str]] | None = None,
):
    """Print system information, tracked env vars, and optional config summary."""
    logger.info("\r\n" * 2)
    console.print(
        "[bold underline]System Information:[/bold underline]"
    )
    system_table = Table(
        show_header=True, header_style="bold cyan"
    )
    system_table.add_column("Property", style="dim")
    system_table.add_column("Value")
    system_info = {
        "Platform": platform.system(),
        "Platform Version": platform.version(),
        "Platform Release": platform.release(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python Version": platform.python_version(),
    }
    for key, value in system_info.items():
        system_table.add_row(key, value)
    console.print(system_table)
    tracked_env = _collect_tracked_env_vars()
    console.print(
        "\n[bold underline]Environment Variable Settings:[/bold underline]"
    )
    if tracked_env:
        env_table = Table(
            show_header=True, header_style="bold green"
        )
        env_table.add_column("Variable", style="dim")
        env_table.add_column("Value")
        for key, value in tracked_env:
            env_table.add_row(key, value)
        console.print(env_table)
    else:
        console.print("[dim]No tracked overrides detected.[/]")

    if config_snapshot:
        console.print(
            "\n[bold underline]Config Snapshot:[/bold underline]"
        )
        cfg_table = Table(
            show_header=True, header_style="bold magenta"
        )
        cfg_table.add_column("Key", style="dim")
        cfg_table.add_column("Value")
        for key, value in config_snapshot:
            cfg_table.add_row(key, value)
        console.print(cfg_table)
    logger.info("\n" * 2)
    console.print()


def _collect_tracked_env_vars() -> list[Tuple[str, str]]:
    rows: list[Tuple[str, str]] = []
    for key in sorted(os.environ):
        if key.startswith(_TRACKED_PREFIXES):
            value = os.environ.get(key, "")
            if key.endswith("API_KEY") and value:
                value = _mask_secret(value)
            rows.append((key, value or "<empty>"))
    return rows


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return value[:1] + "***"
    return f"{value[:4]}…{value[-4:]}"
