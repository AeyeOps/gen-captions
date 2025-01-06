"""A module to print system information and environment variable settings."""

import os
import platform
from logging import Logger

from rich.console import Console
from rich.table import Table


def print_system_info(console: Console, logger: Logger):
    """Print system information and environment variable settings."""
    logger.info("\r\n" * 2)
    console.print("[bold underline]System Information:[/bold underline]")
    system_table = Table(show_header=True, header_style="bold cyan")
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
    console.print(
        "\n[bold underline]Environment Variable Settings:[/bold underline]"
    )
    env_table = Table(show_header=True, header_style="bold green")
    env_table.add_column("Variable", style="dim")
    env_table.add_column("Value")
    for key, value in os.environ.items():
        if key.startswith("GETCAP_"):
            env_table.add_row(key, value)
    console.print(env_table)
    logger.info("\n" * 2)
    console.print()
