"""Command-line interface for the caption generator."""

import os

import typer
from rich.console import Console

from .config import Config
from .encoding_fixer import fix_encoding_issues
from .image_processor import process_images
from .logger_config import CustomLogger
from .system_info import print_system_info

# Module-level initialization
console = Console()
config = Config()
logger = CustomLogger(
    console=console, name="gen_captions", level=config.LOG_LEVEL
).logger

app = typer.Typer(
    help=f"Caption Generator v{config.VERSION} - "
    "Generate image captions with OpenAI or GROK.",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Display top-level help when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(help="Show the current version.")
def version():
    """Display the application version."""
    console.print(f"Caption Generator v{config.VERSION}")


# Config command group
config_app = typer.Typer(
    help="Manage YAML configuration files"
)
app.add_typer(config_app, name="config")


@config_app.command(
    help="Initialize a new local configuration file"
)
def init(
    path: str = typer.Option(
        None,
        help="Output path for config file",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing file",
    ),
):
    """Initialize a new local configuration file."""
    from pathlib import Path

    from .config_manager import ConfigManager

    manager = ConfigManager(console)

    output_path = (
        Path(path) if path else manager.LOCAL_CONFIG_PATH
    )

    if output_path.exists() and not force:
        console.print(
            f"[yellow]Config file already exists:[/] "
            f"{output_path}"
        )
        console.print("Use --force to overwrite")
        raise typer.Exit(code=1)

    created_path = manager.create_local_config_template(
        output_path
    )
    console.print(
        f"[green]Created configuration file:[/] "
        f"{created_path}"
    )
    console.print(
        "\n[bold]Next steps:[/]"
        "\n1. Edit the file to customize settings"
        "\n2. Remove sections you don't want to override"
        "\n3. Set API keys as environment variables:\n"
        "   export OPENAI_API_KEY=sk-..."
        "   export GROK_API_KEY=xai-..."
    )


@config_app.command(help="Show current configuration")
def show(
    backend: str = typer.Option(
        None,
        help="Show config for specific backend",
    ),
):
    """Display current merged configuration."""
    import yaml
    from rich.syntax import Syntax

    config_dict = config._yaml_config

    if backend:
        backends = config_dict.get("backends", {})
        if backend not in backends:
            console.print(
                f"[red]Unknown backend:[/] {backend}"
            )
            raise typer.Exit(code=1)
        config_dict = {backend: backends[backend]}

    # Pretty print as YAML
    yaml_str = yaml.dump(
        config_dict,
        default_flow_style=False,
        sort_keys=False,
    )
    syntax = Syntax(
        yaml_str, "yaml", theme="monokai", line_numbers=True
    )
    console.print(syntax)


@config_app.command(help="Get a configuration value")
def get(
    key: str = typer.Argument(
        ...,
        help="Configuration key (dot notation: "
        "processing.log_level)",
    ),
):
    """Get a specific configuration value."""
    keys = key.split(".")
    value = config._yaml_config

    try:
        for k in keys:
            value = value[k]
        console.print(f"[cyan]{key}:[/] {value}")
    except (KeyError, TypeError):
        console.print(f"[red]Key not found:[/] {key}")
        raise typer.Exit(code=1)


@config_app.command(help="Set a configuration value")
def set_value(
    key: str = typer.Argument(
        ..., help="Configuration key (dot notation)"
    ),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration value in local config."""
    from .config_manager import ConfigManager

    console.print(
        "[yellow]Note:[/] This modifies your local "
        "config file"
    )

    manager = ConfigManager(console)

    try:
        manager.set_config_value(key, value)
        console.print(f"[green]Updated:[/] {key} = {value}")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/] {e}")
        console.print(
            "Run [cyan]gen-captions config init[/] first"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1)


@config_app.command(help="Show config file paths")
def path():
    """Show the active configuration file paths."""
    from .config_manager import ConfigManager

    manager = ConfigManager(console)

    console.print("[bold]Default config:[/]")
    console.print(f"  {manager.get_default_config_path()}")

    local = manager.find_local_config()
    console.print("\n[bold]Local config:[/]")
    if local:
        console.print(f"  {local}")
    else:
        console.print("  (none found)")

    console.print("\n[bold]Local config path:[/]")
    exists = "✓" if manager.LOCAL_CONFIG_PATH.exists() else "✗"
    console.print(f"  {exists} {manager.LOCAL_CONFIG_PATH}")


@config_app.command(help="Validate configuration")
def validate():
    """Validate the current configuration."""
    from .config_manager import ConfigManager

    manager = ConfigManager(console)
    config_dict = manager.get_config()
    errors = manager.validate_config(config_dict)

    if not errors:
        console.print("[green]✓ Configuration is valid[/]")
    else:
        console.print(
            "[red]✗ Configuration validation failed:[/]"
        )
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)


@config_app.command(help="Reset to default configuration")
def reset(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation",
    ),
):
    """Reset local configuration to defaults."""
    from .config_manager import ConfigManager

    manager = ConfigManager(console)
    local_path = manager.find_local_config()

    if not local_path:
        console.print("[yellow]No local config to reset[/]")
        return

    if not force:
        confirm = typer.confirm(
            f"Delete {local_path} and reset to defaults?"
        )
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit()

    local_path.unlink()
    console.print(f"[green]Deleted:[/] {local_path}")
    console.print("Now using default configuration")


@app.command(help="Fix encoding issues in text files.")
def fix_encoding(
    caption_dir: str = typer.Option(
        ..., help="Captions directory for generated text."
    ),
    config_dir: str = typer.Option(
        ..., help="AI toolkit configuration folder."
    ),
):
    """Fix encoding issues in text files."""
    caption_directory = (
        os.path.abspath(caption_dir) if caption_dir else None
    )
    config_directory = (
        os.path.abspath(config_dir) if config_dir else None
    )

    print_system_info(console, logger)
    console.print()

    # If the directories are not provided, print a warning and exit
    if not caption_directory or not config_directory:
        logger.error(
            "Error: Both --caption-dir and --config-dir are required."
        )
        raise typer.Exit(code=1)

    fix_encoding_issues(
        console=console,
        caption_dir=caption_directory,
        config_dir=config_directory,
        logger=logger,
    )


@app.command(
    help="Generate image captions using vision-capable AI models."
)
def generate(
    image_dir: str = typer.Option(..., help="Image directory."),
    caption_dir: str = typer.Option(
        ..., help="Captions directory for generated text."
    ),
    model_profile: str = typer.Option(
        ...,
        help="Model profile: openai, grok, lmstudio, or ollama.",
    ),
):
    """Generate image descriptions using cloud or local AI models.

    Supports cloud providers (OpenAI, GROK) and local servers
    (LM Studio, Ollama).
    """
    print_system_info(console, logger)

    image_directory = (
        os.path.abspath(image_dir) if image_dir else None
    )
    caption_directory = (
        os.path.abspath(caption_dir) if caption_dir else None
    )

    # Validate model profile
    valid_profiles = ["openai", "grok", "lmstudio", "ollama"]
    if model_profile.lower() not in valid_profiles:
        logger.error(
            f"Error: Invalid model profile '{model_profile}'. "
            f"Choose from: {', '.join(valid_profiles)}"
        )
        raise typer.Exit(code=1)

    config.set_backend(model_profile)

    # Verify API key for cloud providers only
    if model_profile.lower() not in ("lmstudio", "ollama"):
        if not config.LLM_API_KEY:
            logger.error("LLM_API_KEY is not set in the environment")
            raise typer.Exit(code=1)

    if not image_directory:
        logger.error("Error: --image-dir is required")
        raise typer.Exit(code=1)

    if caption_directory:
        os.makedirs(caption_directory, exist_ok=True)

    process_images(
        image_directory,
        caption_directory,
        backend=model_profile,
        config=config,
        console=console,
        logger=logger,
    )


@app.command(
    help="Interactive duplicate image detection and cleanup."
)
def dedupe(
    image_dir: str = typer.Option(
        ".",
        "--image-dir",
        help="Directory containing images to deduplicate (default: current directory)"
    ),
    yolo: bool = typer.Option(
        False,
        "--yolo",
        help="Auto-execute all recommendations without prompting"
    ),
):
    """Find and remove duplicate images using multiple detection layers.

    Detects duplicates from exact byte-for-byte matches to perceptually
    similar images, keeping the best quality version.
    """
    from .dedupe import dedupe_command

    dedupe_command(image_dir=image_dir, yolo=yolo, console=console)


if __name__ == "__main__":
    app()
