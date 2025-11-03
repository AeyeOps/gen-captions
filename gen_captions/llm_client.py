"""Factory method to get an LLM client based on the model profile.

To elaborate on the above code snippet, the get_llm_client
function is a factory method that returns an LLM client based
on the model profile argument. The profile argument specifies
which model profile to use, such as "openai" or "grok".
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

    Supports cloud providers (OpenAI, GROK) and local servers
    (LM Studio, Ollama).

    Args:
        backend: Model profile (openai, grok, lmstudio, ollama)
        config: Configuration instance
        console: Rich console for output
        logger: Logger instance

    Returns:
        Appropriate LLM client instance

    Raises:
        ValueError: If backend is not supported
    """
    backend = backend.lower().strip()
    config.set_backend(backend)

    # Mask API key for local providers
    if backend in ("lmstudio", "ollama"):
        key_preview = "<local-no-key-required>"
    else:
        key_preview = (
            f"{config.LLM_API_KEY[:6]}..."
            if config.LLM_API_KEY
            else "<missing>"
        )

    msg = (
        f"Model Profile: {backend}\nLLM_MODEL: {config.LLM_MODEL}\n"
        f"LLM_API_KEY: {key_preview}\nLLM_BASE_URL: {config.LLM_BASE_URL}"
    )
    logger.info(msg)

    # All backends use OpenAI-compatible client
    if backend in ("openai", "grok", "lmstudio", "ollama"):
        logger.info(
            "Using OpenAI-compatible client for profile: %s", backend
        )
        return OpenAIGenericClient(
            config=config, console=console, logger=logger
        )

    raise ValueError(
        f"Unknown model profile '{backend}'. "
        f"Choose from: openai, grok, lmstudio, ollama"
    )
