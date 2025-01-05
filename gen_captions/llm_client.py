# gen_captions/llm_client.py

from .openai_generic_client import OpenAIGenericClient
from .logger_config import logger
from . import config


def get_llm_client(backend: str):
    """Factory method to get an LLM client based on the backend argument."""
    backend = backend.lower().strip()
    config.set_backend(backend)
    logger.info(
        f"""
Backend: {backend}
LLM_MODEL: {config.LLM_MODEL}
LLM_API_KEY: {config.LLM_API_KEY[:6]}...
LLM_BASE_URL: {config.LLM_BASE_URL}
"""
    )

    if backend == "openai":
        logger.info("Using OpenAI Generic backend for OpenAI.")
        return OpenAIGenericClient()
    elif backend == "grok":
        logger.info("Using OpenAI Generic backend for GROK.")
        return OpenAIGenericClient()
    else:
        logger.warning(
            f"Unknown backend '{backend}' specified; defaulting to OpenAI Generic."
        )
        return OpenAIGenericClient()
