.PHONY: help sync install build clean run test lint format typecheck all

# Default target
help:
	@echo "gen-captions v0.3.0 - Makefile targets"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make sync        - Sync dependencies with uv"
	@echo "  make install     - Install all dependencies including dev/test extras"
	@echo ""
	@echo "Building:"
	@echo "  make build       - Build standalone binary with PyInstaller"
	@echo "  make clean       - Remove build artifacts and cache files"
	@echo ""
	@echo "Running:"
	@echo "  make run         - Run gen-captions CLI (shows help)"
	@echo ""
	@echo "Development:"
	@echo "  make test        - Run test suite with pytest"
	@echo "  make lint        - Run linters (ruff, flake8)"
	@echo "  make format      - Format code with black and isort"
	@echo "  make typecheck   - Run mypy type checking"
	@echo "  make all         - Run format, lint, typecheck, and test"

# Sync dependencies (minimal install)
sync:
	uv sync --python 3.14

# Install all dependencies including extras
install:
	uv sync --all-extras --python 3.14

# Build standalone binary
build: clean
	uv run --python 3.14 pyinstaller gen_captions.spec --clean
	mkdir -p /opt/bin
	cp dist/gen-captions /opt/bin/
	@echo ""
	@echo "Binary built and installed to /opt/bin/gen-captions"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Run the CLI
run:
	uv run --python 3.14 gen-captions --help

# Run tests
test:
	uv run --python 3.14 pytest -v

# Lint code
lint:
	uv run --python 3.14 ruff check .
	uv run --python 3.14 flake8 gen_captions/

# Format code
format:
	uv run --python 3.14 black gen_captions/ tests/
	uv run --python 3.14 isort gen_captions/ tests/

# Type check
typecheck:
	uv run --python 3.14 mypy gen_captions/
	# Note: pytype does not yet support Python 3.14

# Run all quality checks
all: format lint typecheck test
	@echo ""
	@echo "All checks passed!"
