"""A module to manage the configuration of the application.

It encapsulates the configuration settings for the application.
"""

import os
import pkgutil


class Config:
    """A class to manage the configuration of the application.

    It encapsulates the configuration settings for the application.
    """

    def __init__(self):
        """Initialize the configuration settings."""
        ver = pkgutil.get_data(__name__, "VERSION")
        ver = ver.decode("utf-8").strip() if ver else "0.0.0"

        self.DEFAULT_MODELS = {
            "OPENAI": "gpt-4o-mini",
            "GROK": "grok-4",
        }
        self.DEFAULT_BASE_URLS = {
            "OPENAI": "https://api.openai.com/v1",
            "GROK": "https://api.x.ai/v1",
        }

        self._config = {
            "VERSION": ver,
            "LLM_API_KEY": None,
            "LLM_MODEL": None,
            "LLM_BASE_URL": None,
            "THREAD_POOL": int(
                os.getenv("GETCAP_THREAD_POOL", 10)
            ),
            "THROTTLE_RETRIES": int(
                os.getenv("GETCAP_THROTTLE_RETRIES", 10)
            ),
            "THROTTLE_BACKOFF_FACTOR": float(
                os.getenv("GETCAP_THROTTLE_BACKOFF_FACTOR", 2)
            ),
            "LOG_LEVEL": os.getenv("GETCAP_LOG_LEVEL", "INFO"),
            "THROTTLE_SUBMISSION_RATE": float(
                os.getenv("GETCAP_THROTTLE_SUBMISSION_RATE", 1)
            ),
        }

    @property
    def VERSION(self):
        """Return the version of the application."""
        return self._config["VERSION"]

    @property
    def LLM_API_KEY(self):
        """Return the API key for the LLM model."""
        return self._config["LLM_API_KEY"]

    @property
    def LLM_MODEL(self):
        """Return the model name for the LLM model."""
        return self._config["LLM_MODEL"]

    @property
    def LLM_BASE_URL(self):
        """Return the base URL for the LLM model."""
        return self._config["LLM_BASE_URL"]

    @property
    def THREAD_POOL(self):
        """Return the thread pool size."""
        return self._config["THREAD_POOL"]

    @property
    def THROTTLE_RETRIES(self):
        """Return the number of retries for throttling."""
        return self._config["THROTTLE_RETRIES"]

    @property
    def THROTTLE_BACKOFF_FACTOR(self):
        """Return the backoff factor for throttling."""
        return self._config["THROTTLE_BACKOFF_FACTOR"]

    @property
    def LOG_LEVEL(self):
        """Return the logging level."""
        return self._config["LOG_LEVEL"]

    @property
    def THROTTLE_SUBMISSION_RATE(self):
        """Return the submission rate for throttling."""
        return self._config["THROTTLE_SUBMISSION_RATE"]

    def set_backend(self, backend: str):
        """Set the backend configuration based on the specified backend."""
        backend = backend.upper().strip()

        default_model = self.DEFAULT_MODELS.get(backend)
        default_base_url = self.DEFAULT_BASE_URLS.get(backend)
        self._config["LLM_API_KEY"] = os.getenv(
            f"{backend}_API_KEY"
        )
        self._config["LLM_MODEL"] = (
            os.getenv(f"{backend}_MODEL") or default_model
        )
        self._config["LLM_BASE_URL"] = (
            os.getenv(f"{backend}_BASE_URL") or default_base_url
        )

    def get_version(self):
        """Return the current version."""
        return self.VERSION
