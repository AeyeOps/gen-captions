# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**gen-captions** is a Python CLI application for generating detailed image captions using OpenAI-compatible LLM models (OpenAI, GROK). Built with Python 3.14+, managed with `uv`, and packaged as a standalone binary with PyInstaller.

The application processes images in batches using ThreadPoolExecutor, handles rate limiting with exponential backoff, and validates model outputs for a specific `[trigger]` token pattern used in stable diffusion prompts.

## Essential Commands

### Development Setup
```bash
# Install dependencies (minimal)
uv sync

# Install with all extras (dev + test)
uv sync --all-extras
```

### Running the Application
```bash
# View help
uv run gen-captions --help

# Generate captions for images
uv run gen-captions generate \
  --image-dir ./images \
  --caption-dir ./captions \
  --model-profile openai

# Fix text encoding issues
uv run gen-captions fix-encoding \
  --caption-dir ./captions \
  --config-dir ./config

# Generate environment file template
uv run gen-captions gen-env
```

### Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# Run single test file
uv run pytest tests/unit/test_cli.py

# Run specific test function
uv run pytest tests/unit/test_cli.py::test_specific_function -v
```

**Testing Guidelines:**
- **NEVER redirect stdout/stderr** when running manual tests (no `2>&1`, `| tail`, `| head`, etc.)
- **NEVER pipe output** during testing - let the user see real-time progress
- **Use reasonable timeouts** (30-60 seconds for small image sets, not 3+ minutes)
- This allows the user to observe what's happening and catch issues early

### Code Quality
```bash
# Lint (must pass before commits)
uv run ruff check .
uv run flake8 gen_captions/

# Format code
uv run black gen_captions/ tests/
uv run isort gen_captions/ tests/

# Type checking
uv run mypy gen_captions/

# Run all quality checks at once
make all
```

### Building
```bash
# Build standalone binary
uv run pyinstaller gen_captions.spec --clean
# Binary output: dist/gen-captions

# Clean build artifacts
make clean
```

## Architecture

### Core Components

1. **CLI Layer** (`cli.py`)
   - Entry point using Typer framework
   - Three commands: `generate`, `fix-encoding`, `gen-env`
   - Environment loading with fallback chain: `GEN_CAPTIONS_ENV_FILE` → discovered `.env` → process env
   - Initializes Config, Logger, Console singletons at module level

2. **Processing Pipeline** (`image_processor.py`)
   - Scans image directory for `.jpg`, `.jpeg`, `.png` files
   - Skips images with existing caption files
   - Submits batch tasks to ThreadPoolExecutor (size: `GETCAP_THREAD_POOL`)
   - Rate-limits submissions using `GETCAP_THROTTLE_SUBMISSION_RATE`
   - Validates outputs for `[trigger]` token before saving

3. **LLM Client Abstraction**
   - **Factory** (`llm_client.py`): `get_llm_client()` returns client based on backend string
   - **Implementation** (`openai_generic_client.py`): `OpenAIGenericClient` wraps `openai.OpenAI` SDK
   - Handles model-specific quirks via `MODEL_CONFIG` dict (system role support, temperature, max tokens)
   - Retry logic: rate limits (429) with exponential backoff, missing `[trigger]` token
   - Built for OpenAI-compatible endpoints (both OpenAI and GROK use the same client)

4. **Configuration** (`config.py`)
   - Centralized `Config` class with property-based access
   - Backend-specific settings via `set_backend()`: sets `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL` from env vars
   - Default models: `gpt-4o-mini` (OpenAI), `grok-4` (GROK)
   - Throttle settings: retries, backoff factor, submission rate, thread pool size

5. **Logging** (`logger_config.py`)
   - `CustomLogger` wrapper around Python logging
   - Dual handlers: RichHandler for console + ConcurrentRotatingFileHandler for thread-safe file logging
   - Custom filters add ISO timestamps and thread IDs to records
   - Log format: `[timestamp][process][thread][level][module::function] message`

### Key Patterns

- **Multi-backend support via factory pattern**: Both OpenAI and GROK use `OpenAIGenericClient` with different env vars
- **Model quirk handling**: `MODEL_CONFIG` dictionary allows per-model parameter customization (e.g., o1-mini doesn't support system role or temperature)
- **Token validation**: All generated captions MUST contain `[trigger]` or they're rejected and retried
- **Concurrent processing with throttling**: ThreadPoolExecutor + sleep-based rate limiting prevents API overload
- **Rich console integration**: Progress bars, colored output, live status for better UX
- **Environment precedence**: Explicit `GEN_CAPTIONS_ENV_FILE` → discovered `.env` → process env vars

## Configuration & Environment

### YAML Configuration Files

**CRITICAL: Configuration file locations and modification rules**

The application uses a **YAML-based configuration system** with two files:

1. **Default configuration**: `~/.config/gen-captions/default.yaml`
   - Copied from bundled template at `/opt/aeo/gen-captions/gen_captions/default.yaml` on first run
   - **EDIT THIS FILE** for permanent configuration changes
   - **NEVER MODIFY THE BUNDLED TEMPLATE** at `/opt/aeo/gen-captions/gen_captions/default.yaml`
   - After changing the bundled template, copy it: `cp /opt/aeo/gen-captions/gen_captions/default.yaml ~/.config/gen-captions/default.yaml`

2. **Local overrides**: `~/.config/gen-captions/local.yaml`
   - Use for **temporary overrides** or **testing**
   - Deep-merged over default.yaml
   - Survives updates
   - Create if it doesn't exist

**For permanent changes (edit ~/.config/gen-captions/default.yaml):**
```yaml
processing:
  log_level: INFO
backends:
  openai:
    model: gpt-5-mini
```

**For temporary testing (edit ~/.config/gen-captions/local.yaml):**
```yaml
processing:
  log_level: DEBUG  # Override just for testing
```

**Configuration merge behavior:**
- local.yaml overrides default.yaml
- Deep merge: nested keys merged, not replaced
- Log file: `/opt/aeo/gen-captions/gen_captions.log`

### Environment Variables (Legacy - being phased out)

API keys are still loaded from environment:
```bash
# API Configuration
OPENAI_API_KEY=sk-...           # Required for OpenAI
GROK_API_KEY=...                # Required for GROK
```

All other settings should use YAML configuration instead of environment variables.

## Code Style

- **Line length**: 65 characters (Black/Isort configuration)
- **Python version**: 3.14+ required
- **Type hints**: Required for all functions (MyPy enforced)
- **Naming**: `snake_case` for modules/functions, `PascalCase` for classes
- **Docstrings**: Required for public functions, Google-style format
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`)

### Zero-Tolerance Linting Policy

**All code must pass linting with ZERO warnings before commits.** This is strictly enforced:

- **Ruff**: Must show "All checks passed!" with no warnings
- **Flake8**: Must have no output (clean exit)
- **MyPy**: Must show "Success: no issues found"

Run `make lint` and `make typecheck` before every commit. The CI pipeline will reject PRs with any linting warnings or type errors.

**Note**: Pytype is not yet supported for Python 3.14. When Python 3.14 reaches stable release and pytype adds support, it will be added to the type checking workflow.

## Testing Strategy

- **Unit tests** (`tests/unit/`): Test individual components in isolation
- **Integration tests** (`tests/integration/`): Test component interactions (currently stubs)
- **E2E tests** (`tests/e2e/`): Full workflow validation (currently stubs)
- **BDD tests** (`tests/features/`): Behave-style feature files with step definitions

Coverage target: Generated reports in `htmlcov/` after `uv run pytest`

## Adding New LLM Models

To add support for a model with special parameter requirements:

1. Add model configuration to `MODEL_CONFIG` in `openai_generic_client.py`:
```python
MODEL_CONFIG = {
    "your-model-name": {
        "supports_system_role": True,      # Can use separate system message?
        "supports_temperature": True,       # Accepts temperature param?
        "max_tokens_key": "max_tokens",    # Parameter name for token limit
        "max_tokens_value": 200,           # Default token limit
    },
}
```

2. The `_build_chat_request()` method automatically handles model quirks

## Common Gotchas

- **Missing `.env` file**: CLI expects env file or `GEN_CAPTIONS_ENV_FILE` set; module-level import will fail without it
- **No `[trigger]` token**: Model outputs without `[trigger]` are rejected and retried up to `THROTTLE_RETRIES` times
- **Rate limiting**: 429 errors trigger exponential backoff; adjust `THROTTLE_BACKOFF_FACTOR` and `THROTTLE_RETRIES` for your API tier
- **Thread safety**: Use `ConcurrentRotatingFileHandler` for logging in multi-threaded contexts
- **Binary building**: PyInstaller spec includes `VERSION` file via `force-include` in `pyproject.toml`

## Development Workflow

1. Make changes to code
2. Format: `uv run black . && uv run isort .`
3. Lint: `uv run ruff check . && uv run flake8 gen_captions/`
4. Type check: `uv run mypy gen_captions/`
5. Test: `uv run pytest`
6. Commit with conventional commit message
7. PR should pass all CI checks (or run `make all` locally first)
