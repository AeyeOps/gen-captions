# Repository Guidelines

## Project Structure & Module Organization
The core package lives in `gen_captions/`, with `cli.py` exposing the CLI, `image_processor.py` handling batch work, and `openai_generic_client.py` wrapping API calls. Tests sit in `tests/` with `unit/`, `integration/`, `e2e/`, and `features/`; add new suites beside peers. Dependencies are managed in `pyproject.toml` with uv.

## Build, Test, and Development Commands
- `uv run gen-captions --help` – view CLI usage and available commands
- `uv run gen-captions generate --image-dir ./images --caption-dir ./captions --model-profile openai` – generate captions for images
- `uv run pytest` – run the full test suite with coverage
- `uv run pytest tests/unit/` – run only unit tests
- `uv run ruff check .` – run linter checks
- `uv run black .` – apply code formatting
- `uv run mypy gen_captions/` – run type checking
- `uv run pyinstaller gen_captions.spec --clean` – build standalone binary

## Coding Style & Naming Conventions
Use 4-space indentation and Python 3.14 type hints. Black and Isort (line length 65) format code, while Ruff, Flake8, and MyPy enforce linting and type checking. Prefer `snake_case` for modules and functions, `PascalCase` for classes, and lowercase hyphenated CLI flags.

## Testing Guidelines
Pytest powers all suites, orchestrated by uv with coverage enabled. Name files `test_<behavior>.py` and cases `test_<condition>_<expected>()` so discovery stays automatic. Keep fast checks in `tests/unit/`, reserve cross-service flows for `tests/integration/` and `tests/e2e/`, and place shared fixtures under `tests/features/`. Run `uv run pytest` before sending code for review.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits (`feat:`, `fix:`, `chore:`) with present-tense subjects under 72 characters. Reference issues when applicable and update docs or diagrams that drift. PRs should summarize intent, capture test evidence, link issues, and include screenshots when assets change. Request a maintainer review and wait for CI before merging.

## Configuration & Secrets
Store credentials in environment variables or a local `.env` ignored by Git; `OPENAI_API_KEY`, `GETCAP_THREAD_POOL`, and throttle settings mirror the samples in `README.md`. Never commit real keys or service URLs. Use `logger_config.py` to adjust log levels instead of ad-hoc prints. If `OPENAI_MODEL` or `OPENAI_BASE_URL` are omitted, the CLI falls back to `gpt-4o-mini` and `https://api.openai.com/v1`; set `GEN_CAPTIONS_ENV_FILE` if you need a non-default env file for CI or staging.
