# Image Caption Generator

Generate detailed captions for image datasets using OpenAI-compatible models with rich logging, retry handling, and CLI utilities.

**Version:** 0.3.0
**Python:** 3.14+
**License:** MIT

## Features

- **Multi-backend LLM support**: Works with OpenAI, GROK, and any OpenAI-compatible API
- **Robust error handling**: Automatic retries with exponential backoff for rate limits and API errors
- **Concurrent processing**: Multi-threaded image processing with configurable thread pools
- **Smart validation**: Validates model outputs for required trigger tokens before saving
- **Encoding utilities**: Fix text encoding issues across caption and configuration files
- **Standalone binary**: Build self-contained executables with PyInstaller
- **Rich console output**: Beautiful progress bars and colored status messages
- **Comprehensive logging**: Thread-safe concurrent logging with rotation
- **Environment-aware**: Flexible configuration via environment files or variables

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Building](#building)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

1. **Python 3.14+** (release candidate supported)
2. **uv package manager** - Install via:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **API Key** - OpenAI API key or compatible service credentials

### Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd gen-captions

# Install minimal dependencies
make sync
# or: uv sync --python 3.14

# Install all dependencies (includes dev and test tools)
make install
# or: uv sync --all-extras --python 3.14
```

## Quick Start

### 1. Configure Environment

Create a `.env` file in the project root:

```bash
# Generate a template .env file
uv run --python 3.14 gen-captions gen-env
```

Edit the generated `.env` file with your credentials:

```properties
# Required: API credentials
OPENAI_API_KEY=sk-your-key-here

# Optional: Model configuration
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
GROK_API_KEY=xai-your-key-here
GROK_MODEL=grok-4
GROK_BASE_URL=https://api.x.ai/v1

# Optional: Performance tuning
GETCAP_THREAD_POOL=50
GETCAP_THROTTLE_SUBMISSION_RATE=10
GETCAP_THROTTLE_RETRIES=100
GETCAP_THROTTLE_BACKOFF_FACTOR=2
GETCAP_LOG_LEVEL=INFO
```

**Note**: The `.env` file is gitignored by default. Never commit API keys to version control.

### 2. Generate Captions

```bash
# Basic usage with OpenAI
uv run --python 3.14 gen-captions generate \
  --image-dir ./images \
  --caption-dir ./captions \
  --llm-backend openai

# Using GROK instead
uv run --python 3.14 gen-captions generate \
  --image-dir ./images \
  --caption-dir ./captions \
  --llm-backend grok
```

**What happens:**
- Scans `./images` for `.jpg`, `.jpeg`, `.png` files
- Generates captions using the specified LLM backend
- Saves captions as `.txt` files in `./captions` directory
- Skips images that already have caption files
- Shows progress bar and detailed logging

## Usage

### Available Commands

```bash
# View all available commands
uv run --python 3.14 gen-captions --help

# Or using make
make run
```

### Command Reference

#### Generate Captions

Generate image captions using OpenAI or GROK models:

```bash
uv run --python 3.14 gen-captions generate \
  --image-dir <path-to-images> \
  --caption-dir <output-directory> \
  --llm-backend <openai|grok>
```

**Options:**
- `--image-dir`: Directory containing source images (required)
- `--caption-dir`: Directory for output caption files (required)
- `--llm-backend`: LLM provider to use: `openai` or `grok` (required)

#### Fix Encoding Issues

Fix text encoding problems in caption and configuration files:

```bash
uv run --python 3.14 gen-captions fix-encoding \
  --caption-dir <captions-directory> \
  --config-dir <config-directory>
```

Attempts to read files with multiple encodings (utf-8, latin1, cp1252) and converts everything to UTF-8.

#### Generate Environment File

Create a new `.env` file with all configuration variables:

```bash
uv run --python 3.14 gen-captions gen-env
```

Creates `.env`, `.env1`, `.env2`, etc. (increments to avoid overwriting existing files).

## Configuration

### Environment Variable Discovery

The CLI loads environment variables in this order (first match wins):

1. File path specified by `GEN_CAPTIONS_ENV_FILE` environment variable
2. `.env` file discovered from current working directory
3. Existing process environment variables

**Example: Override environment file location**
```bash
export GEN_CAPTIONS_ENV_FILE=/path/to/production.env
uv run --python 3.14 gen-captions generate --image-dir ./images --caption-dir ./captions --llm-backend openai
```

### Configuration Variables

#### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | OpenAI API endpoint | `https://api.openai.com/v1` |
| `GROK_API_KEY` | GROK API key | (required for GROK) |
| `GROK_MODEL` | GROK model name | `grok-4` |
| `GROK_BASE_URL` | GROK API endpoint | (none) |

#### Processing Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GETCAP_THREAD_POOL` | Number of concurrent workers | `10` |
| `GETCAP_THROTTLE_SUBMISSION_RATE` | Tasks submitted per second | `1` |
| `GETCAP_THROTTLE_RETRIES` | Maximum retry attempts | `10` |
| `GETCAP_THROTTLE_BACKOFF_FACTOR` | Exponential backoff multiplier | `2` |
| `GETCAP_LOG_LEVEL` | Logging verbosity | `INFO` |

## Development

### Development Workflow

This project uses `make` for all development tasks. See available targets:

```bash
make help
```

### Common Development Tasks

```bash
# Format code with black and isort
make format

# Run linters (ruff + flake8)
make lint

# Run type checker (mypy)
make typecheck

# Run test suite
make test

# Run all quality checks (format + lint + typecheck + test)
make all

# Clean build artifacts
make clean
```

### Code Quality Standards

**Zero-tolerance linting policy**: All code must pass with zero warnings before commits.

- **Ruff**: Must show "All checks passed!"
- **Flake8**: Must have clean exit (no output)
- **MyPy**: Must show "Success: no issues found"

Run `make lint` and `make typecheck` before every commit.

### Code Style

- **Line length**: 65 characters (Black configuration)
- **Python version**: 3.14+
- **Type hints**: Required for all functions
- **Naming**: `snake_case` for modules/functions, `PascalCase` for classes
- **Docstrings**: Google-style format for public APIs
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `chore:`, etc.)

### Running Individual Tools

```bash
# Linting
uv run --python 3.14 ruff check .
uv run --python 3.14 flake8 gen_captions/

# Formatting
uv run --python 3.14 black gen_captions/ tests/
uv run --python 3.14 isort gen_captions/ tests/

# Type checking
uv run --python 3.14 mypy gen_captions/

# Testing
uv run --python 3.14 pytest -v
uv run --python 3.14 pytest tests/unit/
uv run --python 3.14 pytest tests/integration/
```

## Building

### Build Standalone Binary

Create a self-contained executable with PyInstaller:

```bash
# Build binary
make build
# or: uv run --python 3.14 pyinstaller gen_captions.spec --clean

# Binary location
ls -lh dist/gen-captions

# Install to system
cp dist/gen-captions ~/bin/
# or: cp dist/gen-captions /usr/local/bin/
```

The binary includes all dependencies and requires no Python installation on the target system.

## Testing

### Test Structure

- **Unit tests** (`tests/unit/`): Test individual components in isolation
- **Integration tests** (`tests/integration/`): Test component interactions
- **End-to-end tests** (`tests/e2e/`): Full workflow validation
- **BDD tests** (`tests/features/`): Behave-style feature specifications

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test suite
uv run --python 3.14 pytest tests/unit/ -v
uv run --python 3.14 pytest tests/integration/ -v
uv run --python 3.14 pytest tests/e2e/ -v

# Run specific test file
uv run --python 3.14 pytest tests/unit/test_cli.py -v

# Run specific test function
uv run --python 3.14 pytest tests/unit/test_cli.py::test_cli_no_args -v

# View coverage report
# HTML report is generated at: htmlcov/index.html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Current Test Coverage

Run `make test` to see current coverage. Target: 70%+ coverage across all modules.

## Troubleshooting

### Common Issues

#### OSError: File not found during CLI import

**Cause**: No `.env` file found and `GEN_CAPTIONS_ENV_FILE` not set.

**Solution**:
```bash
# Create .env file
uv run --python 3.14 gen-captions gen-env
# Then edit .env with your configuration
```

#### Rate limit errors (429)

**Cause**: API rate limiting from OpenAI or GROK.

**Solution**: Adjust throttle settings in `.env`:
```properties
GETCAP_THROTTLE_RETRIES=100
GETCAP_THROTTLE_BACKOFF_FACTOR=3
GETCAP_THROTTLE_SUBMISSION_RATE=5
```

The client automatically retries with exponential backoff.

#### Missing [trigger] token in output

**Cause**: Model didn't include the required `[trigger]` token in response.

**Solution**: The client automatically retries. If persistent:
- Check your model configuration
- Verify the prompt in `gen_captions/openai_generic_client.py`
- Try a different model (e.g., `gpt-4` instead of `gpt-4o-mini`)

#### Python version compatibility error

**Cause**: Wrong Python version detected.

**Solution**: Explicitly specify Python 3.14:
```bash
uv sync --python 3.14
uv run --python 3.14 gen-captions --help
```

Or set the Python version in `.python-version`:
```bash
echo "3.14.0" > .python-version
```

### Debug Logging

Enable verbose logging:

```bash
# In .env file
GETCAP_LOG_LEVEL=DEBUG

# Check log file
tail -f gen_captions.log
```

## Project Structure

```
gen-captions/
├── gen_captions/          # Main package
│   ├── cli.py            # Typer CLI entrypoint
│   ├── config.py         # Configuration management
│   ├── image_processor.py # Batch processing logic
│   ├── openai_generic_client.py # LLM API client
│   ├── llm_client.py     # Client factory
│   ├── logger_config.py  # Logging configuration
│   ├── encoding_fixer.py # Text encoding utilities
│   ├── utils.py          # Helper functions
│   └── VERSION           # Version file
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   ├── e2e/             # End-to-end tests
│   └── features/        # BDD feature specs
├── pyproject.toml       # Project metadata and dependencies
├── gen_captions.spec    # PyInstaller build spec
├── Makefile             # Development commands
├── CLAUDE.md            # AI assistant guidance
├── AGENTS.md            # Development guidelines
└── README.md            # This file
```

## Repository Layout

- **`gen_captions/`** - Source package (CLI, configuration, logging, processing, OpenAI client)
- **`tests/`** - Unit, integration, and behaviour-driven test suites
- **`pyproject.toml`** - Project configuration and dependencies (managed by uv)
- **`gen_captions.spec`** - PyInstaller specification for standalone binary builds
- **`.python-version`** - Python version pinning for uv (3.14.0)
- **`Makefile`** - Common development tasks (format, lint, test, build)
- **`CLAUDE.md`** - Guidance for Claude Code AI assistant
- **`AGENTS.md`** - Development workflow and contribution guidelines

## Contributing

We welcome contributions! Please see:

- **`CONTRIBUTING.md`** - Contribution guidelines (if exists)
- **`AGENTS.md`** - Development workflow and coding standards
- **`CLAUDE.md`** - Architecture documentation and development patterns

### Before Submitting a PR

1. Run `make all` to verify all checks pass
2. Ensure zero linting warnings (ruff, flake8, mypy)
3. Add tests for new functionality
4. Update documentation as needed
5. Use conventional commit messages

## Support

- **Issues**: Report bugs or request features via the repository issue tracker
- **Documentation**: See `CLAUDE.md` for architecture details
- **Development**: See `AGENTS.md` for workflow guidelines

## License

MIT License. See `LICENSE` file for details.

## Acknowledgments

Built with:
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [OpenAI Python SDK](https://github.com/openai/openai-python) - API client
- [PyInstaller](https://pyinstaller.org/) - Binary packaging
