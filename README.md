# Image Caption Generator

Generate detailed captions for image datasets using OpenAI-compatible vision models with rich logging, configurable pipelines, and dataset hygiene utilities.

**Version:** 0.5.2
**Python:** 3.14+
**License:** MIT

## Features

- **Multi-backend LLM support**: Run caption jobs against OpenAI, GROK, LM Studio, or Ollama using a single client.
- **Local readiness checks**: Automatically detect LM Studio/Ollama availability and print step-by-step recovery instructions.
- **YAML-driven configuration**: Ship defaults with `default.yaml`, layer overrides via `config init`, and manage settings entirely from the CLI.
- **Concurrent captioning**: Thread-pooled processing with rate limiting, exponential backoff, and `[trigger]` guardrails.
- **Dataset cleanup**: Interactive duplicate detection with quality scoring and optional YOLO automation.
- **Encoding repair**: Batch fix caption and configuration files to UTF-8 with progress feedback.
- **Structured logging**: Rotating Rich-aware logging plus system diagnostics at command start.
- **Binary distribution**: Produce a standalone executable with PyInstaller via `make build`.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Local Models](#local-models)
- [Development](#development)
- [Building](#building)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Installation

### Prerequisites

1. **Python 3.14+** (3.14.0 RC is supported).
2. **uv package manager** – install with:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **API credentials** – export `OPENAI_API_KEY` or `GROK_API_KEY` when using cloud providers.

### Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd gen-captions

# Install runtime dependencies
make sync
# or: uv sync --python 3.14

# Install all extras for development and testing
make install
# or: uv sync --all-extras --python 3.14
```

The first run copies the bundled `default.yaml` into `~/.config/gen-captions/`.

## Quick Start

1. **Set credentials (cloud backends only)**  
   ```bash
   export OPENAI_API_KEY=sk-your-key
   export GROK_API_KEY=xai-your-key  # optional unless --model-profile grok
   ```

2. **Initialize local overrides (optional but recommended)**  
   ```bash
   uv run gen-captions config init
   ```
   This creates `~/.config/gen-captions/local.yaml`. Edit it to override prompts, models, or processing parameters while keeping defaults untouched. Example:
   ```yaml
   processing:
     thread_pool: 20
     throttle_submission_rate: 2.0

   backends:
     openai:
       model: gpt-5
   ```

3. **Generate captions**
   ```bash
   # OpenAI profile
   uv run gen-captions generate \
     --image-dir ./images \
     --caption-dir ./captions \
     --model-profile openai

   # Local Ollama profile
   uv run gen-captions generate \
     --image-dir ./images \
     --caption-dir ./captions \
     --model-profile ollama
   ```
   The CLI prints system information, validates configuration, skips images with existing captions, and writes UTF-8 `.txt` files that include the `[trigger]` token. Logs are written to `gen_captions.log`.

## Usage

### Command Overview

```bash
uv run gen-captions --help
uv run gen-captions version
uv run gen-captions generate --image-dir ./images --caption-dir ./captions --model-profile openai
uv run gen-captions remove --image-dir ./images --model-profile openai --keep-gender women --keep-solo yes
uv run gen-captions fix-encoding --caption-dir ./captions --config-dir ~/.config/gen-captions
uv run gen-captions dedupe --image-dir ./images [--yolo]
uv run gen-captions config --help
```

### Generate Image Captions

- Required options: `--image-dir`, `--caption-dir`, `--model-profile`.
- Supported profiles: `openai`, `grok`, `lmstudio`, `ollama`.
- Cloud providers require API keys; local providers run against the configured base URL and require no key.
- Uses a thread pool (`processing.thread_pool`) with submission throttling. Retries API calls until `[trigger]` appears or retries are exhausted.
- Captions are saved beside the dataset with one `.txt` per image.

### Remove Mismatched Images

```bash
uv run gen-captions remove \
  --image-dir ./images \
  --model-profile openai \
  --keep-gender women \
  --keep-solo yes
```

- Uses the same backend profiles as `generate` (OpenAI, GROK, LM Studio, Ollama).
- Each analyzed file prints a structured JSON payload with thought + probability scores for solo/men/women.
- Pass at least one filter flag (`--keep-gender` and/or `--keep-solo`).
- Use `--keep-gender women|men` to KEEP only that gender and move the rest to `removed/`.
- `--keep-solo yes|true|1` keeps single-subject shots (removes groups); `--keep-solo no|false|0` keeps group scenes. Leave it off to ignore solo status.
- Captions stored next to their images move automatically into `<image-dir>/removed`, and every decision (probabilities, reasons, action) is logged to `gen_captions.log` alongside the JSON console output.
- Thresholds (default `0.9`) are configurable under the `removal.thresholds` section in the YAML config.

### Deduplicate Dataset

```bash
uv run gen-captions dedupe --image-dir ./images
```

- Runs five detection layers (exact match through perceptual similarity).
- Interactive mode previews recommendations per layer; press `c` to apply all moves, `s` to skip, or `x` to exit.
- `--yolo` applies every recommendation without prompting.
- Moved files land in `<image-dir>/duplicates/`; caption files move with their images. A summary shows items kept, moved, and total space reclaimed.

### Fix Encoding

```bash
uv run gen-captions fix-encoding \
  --caption-dir ./captions \
  --config-dir ~/.config/gen-captions
```

Scans `.txt`, `.yml`, and `.yaml` files, attempts multiple legacy encodings, and rewrites them as UTF-8. Useful after importing datasets from mixed locales.

### Configuration CLI

| Command | Description |
| --- | --- |
| `config init [--path PATH]` | Create a minimal `local.yaml` template (default `~/.config/gen-captions/local.yaml`). |
| `config show [--backend NAME]` | Render the merged configuration with syntax highlighting. |
| `config get <dot.path>` | Print a single value (e.g. `processing.thread_pool`). |
| `config set-value <dot.path> <value>` | Update the local configuration in-place. |
| `config path` | Display effective default/local file paths. |
| `config validate` | Validate structure and configuration version. |
| `config reset [--force]` | Remove the local override and fall back to defaults. |

### Diagnostics & Logging

- `gen-captions version` prints the currently installed version (0.5.2).
- Each command logs to `gen_captions.log` with timestamped, thread-aware entries and mirrors key events to the Rich console.
- `system_info` output (platform, Python, `GETCAP_*` env overrides) prints automatically at the start of long-running commands.

## Configuration

### File Locations

- **Default**: `~/.config/gen-captions/default.yaml` (auto-copied from the package on first run).
- **Local overrides**: `~/.config/gen-captions/local.yaml` (generated via `config init`).
- **Custom location**: Set `GEN_CAPTIONS_CONFIG=/path/to/local.yaml` to use an alternate override file (CI, staging, etc.).

`ConfigManager` merges the default and local files, validating against the schema defined in `gen_captions/config_schema.py`.

### Structure Overview

```yaml
config_version: "1.0"

backends:
  openai:
    model: gpt-5-mini
    base_url: https://api.openai.com/v1
    models:
      gpt-5-mini:
        description: "RECOMMENDED: Cost-efficient GPT-5 with excellent vision capabilities"
  grok:
    model: grok-2-vision-1212
    base_url: https://api.x.ai/v1
  lmstudio:
    model: qwen/qwen2.5-vl-7b
    base_url: http://localhost:1234/v1
  ollama:
    model: qwen2.5vl:7b
    base_url: http://localhost:11434/v1

caption:
  required_token: "[trigger]"
  system_prompt: "You are an expert at generating detailed and accurate stability diffusion type prompts..."
  user_prompt: "Describe the content of this image..."
processing:
  thread_pool: 10
  throttle_submission_rate: 1.0
  throttle_retries: 10
  throttle_backoff_factor: 2.0
  log_level: INFO
```

### Overriding Values

- Use the CLI:  
  ```bash
  uv run gen-captions config set-value processing.thread_pool 16
  uv run gen-captions config set-value backends.ollama.model qwen3-vl:8b
  ```
- Or edit `local.yaml` directly; only include keys you want to override.
- Run `uv run gen-captions config validate` after editing to catch structural mistakes.

### Environment Variables

| Variable | Purpose | When to set |
| --- | --- | --- |
| `OPENAI_API_KEY` | API token for OpenAI profiles | Required for `--model-profile openai` |
| `GROK_API_KEY` | API token for GROK profiles | Required for `--model-profile grok` |
| `GEN_CAPTIONS_CONFIG` | Path to alternate local override | Optional (CI, ephemeral configs) |

LM Studio and Ollama profiles run locally and do not need API keys.

## Local Models

- **LM Studio**  
  1. Launch the app, open the **Local Server** tab, and press **Start Server** (default port `1234`).  
  2. Load a vision-capable model that matches `backends.lmstudio.model`.  
  3. Run `gen-captions generate --model-profile lmstudio`. The client verifies the server and prints guided recovery steps if unreachable.

- **Ollama**  
  1. Start the daemon: `ollama serve` (default port `11434`).  
  2. Pull a supported model, e.g. `ollama pull qwen2.5vl:7b` or `ollama pull openbmb/minicpm-v4.5`.  
  3. Run `gen-captions generate --model-profile ollama`. Connection issues trigger detailed troubleshooting hints.

Use `config show --backend lmstudio` or `--backend ollama` to list the curated model descriptions included with the defaults.

## Development

```bash
uv run ruff check .
uv run flake8 gen_captions/
uv run black gen_captions/ tests/
uv run isort gen_captions/ tests/
uv run mypy gen_captions/
uv run pytest
uv run pytest tests/unit/
make all  # format + lint + typecheck + test
```

Follow the 4-space indentation, Black + Isort (line length 65), and Ruff/MyPy guidelines enforced in `pyproject.toml`.

## Building

```bash
make build
# -> dist/gen-captions packaged and copied to /opt/bin/gen-captions
```

This runs `uv sync --all-extras` first, then uses `pyinstaller` with `gen_captions.spec`. To build manually:

```bash
uv run pyinstaller gen_captions.spec --clean
```

## Testing

- Run the entire suite with coverage:
  ```bash
  uv run pytest
  ```
- Target a suite:
  ```bash
  uv run pytest tests/unit/
  ```
- Coverage HTML reports land in `htmlcov/index.html`.

## Troubleshooting

- **"LLM_API_KEY is not set"** – Export the appropriate API key before running cloud backends.  
  ```bash
  export OPENAI_API_KEY=sk-your-key
  ```

- **Local server connection errors** – The CLI prints backend-specific instructions. For LM Studio, start the Local Server and confirm the port matches `backends.lmstudio.base_url`. For Ollama, ensure `ollama serve` is running and the requested model is pulled.

- **Missing `[trigger]` token** – The client automatically retries. If it persists, adjust `caption.system_prompt`/`caption.user_prompt` or switch to a different model profile.

- **Rate limits or slow throughput** – Tune `processing.thread_pool`, `processing.throttle_submission_rate`, or `processing.throttle_backoff_factor` in `local.yaml`.

- **Configuration validation warnings** – Run `uv run gen-captions config validate`. Ensure `config_version` matches the bundled schema (currently `1.0`).

- **Need deeper logs** – Set `processing.log_level` to `DEBUG` and inspect `gen_captions.log`.

## Project Structure

```
gen-captions/
├── gen_captions/
│   ├── cli.py
│   ├── config.py
│   ├── config_manager.py
│   ├── config_schema.py
│   ├── dedupe.py
│   ├── duplicate_detector.py
│   ├── encoding_fixer.py
│   ├── file_operations.py
│   ├── image_processor.py
│   ├── llm_client.py
│   ├── logger_config.py
│   ├── openai_generic_client.py
│   ├── quality_scorer.py
│   ├── system_info.py
│   ├── utils.py
│   └── default.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── features/
├── docs/
├── Makefile
├── pyproject.toml
├── gen_captions.spec
└── README.md
```

Runtime configuration lives in `~/.config/gen-captions/`, and logs default to `gen_captions.log` in the working directory.

Version metadata is resolved directly from `pyproject.toml`, eliminating the old `VERSION` file duplication.

## Contributing

- Review `CONTRIBUTING.md`, `AGENTS.md`, and `CLAUDE.md`.
- Use Conventional Commits (`feat:`, `fix:`, `chore:`) under 72 characters.
- Run `make all` (or the equivalent uv commands) before opening a PR.
- Add or update tests alongside functional changes.

## Support

Open an issue in the repository for bugs or feature requests. Architecture and workflow references live in `CLAUDE.md` and `AGENTS.md`.

## License

MIT. See `LICENSE` for details.

## Acknowledgments

Built with:

- [uv](https://github.com/astral-sh/uv) – Python packaging/runtime management
- [Typer](https://typer.tiangolo.com/) – CLI framework
- [Rich](https://rich.readthedocs.io/) – Console output & progress bars
- [OpenAI Python SDK](https://github.com/openai/openai-python) – API client
- [imagehash](https://github.com/JohannesBuchner/imagehash) – Perceptual duplicate detection
- [PyInstaller](https://pyinstaller.org/) – Binary packaging
- [Pillow](https://python-pillow.org/) – Image handling
