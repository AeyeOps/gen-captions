import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

LLM_API_KEY = None
LLM_MODEL = None
LLM_BASE_URL = None


def set_backend(backend: str):
    global LLM_API_KEY, LLM_MODEL, LLM_BASE_URL
    backend = backend.upper().strip()
    LLM_API_KEY = os.getenv(f"{backend}_API_KEY")
    LLM_MODEL = os.getenv(f"{backend}_MODEL")
    LLM_BASE_URL = os.getenv(f"{backend}_BASE_URL")


THREAD_POOL = int(os.getenv("GETCAP_THREAD_POOL", 10))
THROTTLE_RETRIES = int(os.getenv("GETCAP_THROTTLE_RETRIES", 10))
THROTTLE_BACKOFF_FACTOR = float(os.getenv("GETCAP_THROTTLE_BACKOFF_FACTOR", 2))
LOG_LEVEL = os.getenv("GETCAP_LOG_LEVEL", "INFO")
THROTTLE_SUBMISSION_RATE = float(os.getenv("GETCAP_THROTTLE_SUBMISSION_RATE", 1))
