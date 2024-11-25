# gen_captions/constants.py

import os
import logging
from dotenv import load_dotenv

# Load environment variables
envs = [".env", ".env.aider", ".env.aider.local", ".env.local"]
for env in envs:
    if os.path.exists(env):
        load_dotenv(
            dotenv_path=env,
            override=True,
            verbose=True)
    else:
        logging.warning(f"Environment file {env} not found.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
THREAD_POOL = int(os.getenv("GETCAP_THREAD_POOL", 10))
THROTTLE_RETRIES = int(os.getenv("GETCAP_THROTTLE_RETRIES", 10))
THROTTLE_BACKOFF_FACTOR = float(os.getenv("GETCAP_THROTTLE_BACKOFF_FACTOR", 2))
LOG_LEVEL = os.getenv("GETCAP_LOG_LEVEL", "INFO")
THROTTLE_SUBMISSION_RATE = float(os.getenv("GETCAP_THROTTLE_SUBMISSION_RATE", 1))
