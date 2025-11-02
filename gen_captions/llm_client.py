"""Factory method to get an LLM client based on the model profile.

To elaborate on the above code snippet, the get_llm_client function is a
factory method that returns an LLM client based on the model profile argument.
The profile argument specifies which model profile to use, such as "openai" or "grok".
"""

from logging import Logger

from rich.console import Console

from .config import Config
from .openai_generic_client import OpenAIGenericClient


def get_llm_client(
    backend: str,
    config: Config,
    console: Console,
    logger: Logger,
):
    """Get an LLM client based on the model profile.

    Depending on the profile specified, returns the corresponding LLM
    client.
    """
    backend = backend.lower().strip()
    config.set_backend(backend)
    key_preview = (
        f"{config.LLM_API_KEY[:6]}..."
        if config.LLM_API_KEY
        else "<missing>"
    )
    msg = (
        f"Model Profile: {backend}\nLLM_MODEL: {config.LLM_MODEL}\nLLM_API_KEY: "
        f"{key_preview}\nLLM_BASE_URL: {config.LLM_BASE_URL}"
    )
    logger.info(msg)

    if backend in ("openai", "grok"):
        logger.info(
            "Using OpenAI Generic client for profile: %s", backend
        )
        return OpenAIGenericClient(
            config=config, console=console, logger=logger
        )

    raise ValueError(f"Unknown model profile '{backend}' specified.")
