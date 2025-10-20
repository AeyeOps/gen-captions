# Repository Guidelines

## Project Structure & Module Organization
The core package lives in `gen_captions/`, with `cli.py` exposing the CLI, `image_processor.py` handling batch work, and `openai_generic_client.py` wrapping API calls. Tests sit in `tests/` with `unit/`, `integration/`, `e2e/`, and `features/`; add new suites beside peers. Dependency manifests reside in `requirements/`, and `setup_env.sh` bootstraps a virtual environment when Pants is not in use.

## Build, Test, and Development Commands
- `pants run gen_captions:gen-captions -- --image-dir ./images --caption-dir ./captions --config-dir ./config` executes the CLI with passthrough flags.
- `pants test ::` runs every pytest target with coverage; focus with paths like `tests/unit::`.
- `pants lint ::` and `pants fmt ::` enforce the configured Python and shell linters.
- `pants package gen_captions:gen-captions` produces a self-contained PEX.
- `./setup_env.sh` provisions `venv/` and installs `requirements.txt` for a lightweight workflow.

## Coding Style & Naming Conventions
Use 4-space indentation and Python 3.11 type hints. Black and Isort (line length 65) run via `pants fmt`, while Flake8, Pylint, Bandit, Docformatter, and Pyupgrade back `pants lint`. Prefer `snake_case` for modules and functions, `PascalCase` for classes, and lowercase hyphenated CLI flags.

## Testing Guidelines
Pytest powers all suites, orchestrated by Pants with coverage enabled. Name files `test_<behavior>.py` and cases `test_<condition>_<expected>()` so discovery stays automatic. Keep fast checks in `tests/unit/`, reserve cross-service flows for `tests/integration/` and `tests/e2e/`, and place shared fixtures under `tests/features/`. Run `pants test ::` before sending code for review.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits (`feat:`, `fix:`, `chore:`) with present-tense subjects under 72 characters. Reference issues when applicable and update docs or diagrams that drift. PRs should summarize intent, capture test evidence, link issues, and include screenshots when assets change. Request a maintainer review and wait for CI before merging.

## Configuration & Secrets
Store credentials in environment variables or a local `.env` ignored by Git; `OPENAI_API_KEY`, `GETCAP_THREAD_POOL`, and throttle settings mirror the samples in `README.md`. Never commit real keys or service URLs. Use `logger_config.py` to adjust log levels instead of ad-hoc prints.
If `OPENAI_MODEL` or `OPENAI_BASE_URL` are omitted, the CLI falls back to
`gpt-4o-mini` and `https://api.openai.com/v1`; set `GEN_CAPTIONS_ENV_FILE`
if you need a non-default env file for CI or staging.
