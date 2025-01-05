import os
import typer
from rich.console import Console
from dotenv import dotenv_values
from pathlib import Path

from . import config
from .logger_config import logger
from .system_info import print_system_info
from .encoding_fixer import fix_encoding_issues
from .image_processor import process_images

console = Console()


app = typer.Typer(
    help="Caption Generator v1.0.5 - Generate image captions with OpenAI or GROK.",
)


@app.command(help="Generate an environment file.")
def gen_env():
    """
    Generate a .env-like file with environment variables used in this codebase.
    If .env exists, create .env1, if that exists, create .env2, and so on.
    Populate with values from any existing .env if present, or use defaults.
    """
    # Ordered list of environment variables (existing defaults + discovered)
    env_keys = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "GROK_API_KEY",
        "GROK_MODEL",
        "GROK_BASE_URL",
        "GETCAP_THREAD_POOL",
        "GETCAP_THROTTLE_SUBMISSION_RATE",
        "GETCAP_THROTTLE_RETRIES",
        "GETCAP_THROTTLE_BACKOFF_FACTOR",
        "GETCAP_LOG_LEVEL",
    ]

    existing = {}
    base_env_file = Path(".env")
    if base_env_file.exists():
        existing = dotenv_values(dotenv_path=str(base_env_file))

    # Find a new file name that doesn't overwrite anything
    counter = 0
    new_file = Path(".env")
    while new_file.exists():
        counter += 1
        new_file = Path(f".env{counter}")

    # Write to the new file
    with new_file.open("w") as f:
        for key in env_keys:
            # Use existing value if present; else fallback to a placeholder or default
            f.write(f"{key}={existing.get(key, '')}\n")

    print(f"Created {new_file} with collected environment variables.")


@app.command(help="Fix encoding issues in text files.")
def fix_encoding(
    caption_dir: str = typer.Option(..., help="Captions directory for generated text."),
    config_dir: str = typer.Option(..., help="AI toolkit configuration folder."),
):
    """
    Fix encoding issues in text files.
    """
    caption_directory = os.path.abspath(caption_dir) if caption_dir else None
    config_directory = os.path.abspath(config_dir) if config_dir else None

    print_system_info()
    console.print()
    fix_encoding_issues(caption_dir=caption_directory, config_dir=config_directory)


@app.command(help="Generate image captions with OpenAI or GROK.")
def generate(
    image_dir: str = typer.Option(..., help="Image directory."),
    caption_dir: str = typer.Option(..., help="Captions directory for generated text."),
    llm_backend: str = typer.Option(..., help="Choose LLM backend: openai or grok."),
):
    print_system_info()
    console.print()

    image_directory = os.path.abspath(image_dir) if image_dir else None
    caption_directory = os.path.abspath(caption_dir) if caption_dir else None

    if llm_backend not in ["openai", "grok"]:
        logger.error("Error: --llm-backend must be either 'openai' or 'grok'.")
        raise typer.Exit(code=1)
    config.set_backend(llm_backend)

    if not config.LLM_API_KEY:
        logger.error("LLM_API_KEY is not set in the environment")
    else:
        if not image_directory:
            logger.error("Error: --image-dir is required if not using --fix-encoding.")
            raise typer.Exit(code=1)

        # Pass the chosen backend to the process_images function
        process_images(image_directory, caption_directory, backend=llm_backend)


if __name__ == "__main__":
    app()
