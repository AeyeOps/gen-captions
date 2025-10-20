# Image Caption Generator

Generate detailed captions for image datasets using OpenAI-compatible models with rich logging, retry handling, and CLI utilities.

## Overview
The project packages the captioning workflow as a Pants-managed Python application. The entrypoint (`gen_captions.cli`) exposes commands for generating captions, fixing text encoding, and scaffolding environment files. Supporting modules handle configuration, logging, API access, and image batching.

## Repository Layout
- `gen_captions/` – source package (CLI, configuration, logging, processing, OpenAI client).
- `tests/` – unit, integration, and behaviour-driven test suites.
- `requirements/` – lockfiles for runtime, dev, and test dependencies.
- `pants.toml` – Pants build configuration.
- `setup_env.sh` – optional helper to bootstrap a virtual environment outside Pants.

## Prerequisites
- Python 3.11+
- An OpenAI API key (or compatible gateway URL/key)
- Pants launcher (`pants` on your PATH) – install via:
  ```bash
  curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  ```

## Environment Configuration
The CLI loads environment variables from (in order):
1. A file path specified by `GEN_CAPTIONS_ENV_FILE`.
2. The nearest `.env` discovered from the working directory.
3. Existing process environment variables.

Create a `.env` (or `.env.local`) in the repository root to develop locally:
```properties
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini        # optional; defaults to gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1  # optional; defaults to this URL
GETCAP_THREAD_POOL=50
GETCAP_THROTTLE_SUBMISSION_RATE=10
GETCAP_THROTTLE_RETRIES=100
GETCAP_THROTTLE_BACKOFF_FACTOR=2
GETCAP_LOG_LEVEL=INFO
```
The file is `.gitignore`-d; keep secrets out of version control.

Tip: point `GEN_CAPTIONS_ENV_FILE` at a specific env file (e.g. CI secrets) when you
need to override the default discovery order.

## Quick Start
```bash
# View CLI usage
pants run gen_captions:gen-captions -- --help

# Generate captions (writes .txt files into ./captions)
pants run gen_captions:gen-captions -- generate \
  --image-dir ./images \
  --caption-dir ./captions \
  --llm-backend openai

# Fix encoding issues across caption/config directories
pants run gen_captions:gen-captions -- fix-encoding \
  --caption-dir ./captions \
  --config-dir ./config

# Produce a new .env file with discovered keys
pants run gen_captions:gen-captions -- gen-env
```

## Development Workflow
Pants orchestrates linting, formatting, packaging, and tests:
- `pants lint ::` – run Flake8, Pylint, pydocstyle, etc.
- `pants fmt ::` – apply Black, Isort, and related formatters.
- `pants test ::` – execute every pytest target with coverage.
- `pants package gen_captions:gen-captions` – build a PEX binary.

When coding outside Pants, `./setup_env.sh` creates `venv/` and installs `requirements.txt`.

## Testing
Pytest backs unit/integration tests, while Behave-style feature steps live under `tests/features/`. Target specific scopes when iterating:
```bash
pants test tests/unit::
pants test tests/integration::
```

## Troubleshooting
- **`OSError: File not found` during CLI import** – ensure a `.env` (or `GEN_CAPTIONS_ENV_FILE`) is accessible when running outside Pants' sandbox.
- **Rate limit errors** – adjust `GETCAP_THROTTLE_*` variables; the client retries with exponential backoff.
- **Missing `[trigger]` token** – the OpenAI client retries automatically; check model output or update prompts in `openai_generic_client.py`.

## Contributing & Support
See `CONTRIBUTING.md` and `AGENTS.md` for workflow guidelines. Report issues or questions via the repository issue tracker.

## License
MIT License. Refer to `LICENSE` for details.
