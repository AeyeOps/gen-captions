# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2025-02-02

### Removed

* **VSCode Debug Configuration**
  Removed the `"Python: Current File"` debug configuration from `.vscode/launch.json`.

### Changed

* **CLI & Environment Loading**
  * Updated `gen_captions/cli.py` to:
    * Use `find_dotenv` and `load_dotenv` for environment variable loading.
    * Switch to using `console.print(...)` instead of raw `print(...)`.
  * Removed extraneous `load_dotenv` call from `config.py`.
* **fix_encoding Command**
  * Enhanced `fix_encoding_issues` function (in `gen_captions/encoding_fixer.py`) to accept typed parameters, show a progress bar, and log scanning details.
* **Image Processing**
  * Moved most logic for scanning directories, skipping existing .txt prompts, and using a single `Progress` bar into `gen_captions/image_processor.py`.
  * Now prints messages indicating how many images are skipped or processed, and uses **Rich** for progress tracking.
* **Logger Configuration**
  * Consolidated the logging configuration into `logger_config.py`, removing older docstrings and unused code.
  * Added `ConcurrentRotatingFileHandler` usage for concurrency-safe log rotation.
  * Exposed a `CustomLogger` with date/time formatting, thread IDs, and a single log handler.
* **OpenAI Generic Client**
  * Reworked `openai_generic_client.py` to:
    * Dynamically build request parameters for different model quirks (e.g., `o1-mini`, `o3-mini`).
    * Retry if response is missing `[trigger]`.
    * Print success/error messages to the console.
* **Lockfile Updates**
  * Upgraded multiple dependencies in `gen_captions/lockfile.lock`, including:
    * `attrs` from `24.3.0` → `25.1.0`
    * `black` from `24.10.0` → `25.1.0`
    * `cachetools` from `5.5.0` → `5.5.1`
    * `certifi` from `2024.12.14` → `2025.1.31`
    * `concurrent_log_handler` newly added at `0.9.25`
    * `filelock` from `3.16.1` → `3.17.0`
    * `fsspec` from `2024.12.0` → `2025.2.0`
    * `huggingface_hub` from `0.27.1` → `0.28.1`
    * `isort` from `5.13.2` → `6.0.0`
    * `numpy` from `2.2.1` → `2.2.2`
    * `openai` from `1.59.6` → `1.61.0`
    * `pydantic` from `2.10.5` → `2.10.6`
    * `pyproject_api` from `1.8.0` → `1.9.0`
    * `torch` from `2.5.1` → `2.6.0`
    * `transformers` from `4.48.0` → `4.48.2`
    * `triton` from `3.1.0` → `3.2.0`
    * `virtualenv` from `20.28.1` → `20.29.1`
  * Added or updated references to `nvidia-cusparselt-cu12==0.6.2` for Linux x86_64 and a new `portalocker` dependency.
* **Dependency Changes**
  * Added `concurrent_log_handler` to `requirements/requirements.txt`.

### Added

* **`gen_changelog.sh` Script**
  * A new script to automatically generate or copy diffs for changelog entries.
* **Tests & BUILD Files**
  * Created or updated test targets in `tests/BUILD`, `tests/e2e/BUILD`, `tests/features/steps/BUILD`, and `tests/integration/BUILD`.
  * Introduced new test files:
    * `tests/unit/test_encoding_fixer.py`
    * `tests/unit/test_image_processor.py`
    * `tests/unit/test_openai_api.py`
    * `tests/unit/test_utils.py`
  * Removed older test stubs (e.g., `test_cli.py`, `test_utils.py`) and replaced them with updated versions or consolidated them in “unit” subfolders.

### Removed

* **Obsolete Test Files**
  * Deleted legacy test files like `test_encoding_fixer.py`, `test_image_processor.py`, and `test_openai_api.py` at the top-level.
  * Replaced them with updated or reorganized versions in unit/integration/e2e directories.

## [0.2.1] - 2025-02-01

### Added

- **VSCode Debug Configuration**Added a new Python debug configuration to `.vscode/launch.json` (lines enabling `debugpy` with an integrated terminal).
- **Workspace Updates**Updated `gen-captions.code-workspace` to include a reference/path to `../pants-plugins`.
- **Behave Dependencies**In `gen_captions/lockfile.lock`, introduced dependencies for `behave`, `parse`, and `parse-type`.
- **New Integration Test Stub**
  A new file `tests/integration/test_integration_stub.py` was added (currently empty) for integration test scaffolding.

### Changed

- **Removed Pytest Backend**Removed `"pants.backend.python.test.pytest"` from `pants.toml`, so Pants no longer uses the older Python test backend directly.
- **Dependency Upgrades**
  - `huggingface_hub` from `0.27.0` to `0.27.1`
  - `openai` from `1.59.3` to `1.59.6`
  - `pydantic` from `2.10.4` to `2.10.5`
  - `pygments` from `2.19.0` to `2.19.1`
  - `libcst` from `1.5.1` to `1.6.0`
  - `safetensors` from `0.5.0` to `0.5.2`
  - `setuptools` from `75.7.0` to `75.8.0`
  - `transformers` from `4.47.1` to `4.48.0`
  - `six` version pinned at `1.17.0`
  - `torch` pinned to `>=2.0`
  - Updated references to `codecarbon` to use `>=2.8.1`
- **Refactored Build Targets**
  - Changed `tests/e2e/BUILD`, `tests/integration/BUILD`, and `tests/unit/BUILD` to rename or indent `python_tests` targets properly.
  - Replaced `behave_tests(...)` with `python_tests(...)` in `tests/features/BUILD`.
- **File Renames & Indentation**
  - Renamed `tests/__init__.py` → `tests/e2e/test_e2e_stub.py`.
  - Indentation and code-style adjustments across multiple BUILD files.
- **Behave Step Definitions**
  - Updated `tests/features/steps/steps_generate_captions.py` to use `from behave import given, then, when` and adjusted the decorator strings.
- **Tests**
  - Minor enhancements to `tests/unit/test_config.py` to patch environment variables more explicitly.

### Removed

- **Obsolete or Redundant References**
  - Removed the direct `[python.test.pytest]` reference in `pants.toml`.

## [0.2.0] - 2024-12-15

### Added

- Initial setup for the project with basic functionality to generate captions using OpenAI's API.
- Added support for fixing encoding issues in text files.
- Implemented logging configuration and environment variable management.

### Changed

- Updated README.md with detailed usage instructions and a workflow diagram.

### Fixed

- Resolved issues with API rate limiting by implementing exponential backoff.

## [1.0.5] - 2024-11-24

### Added

- Added support for asynchronous image processing with a thread pool.
- Introduced command-line interface for easier configuration and execution.
- Added tests for core functionalities using `pytest`.

### Changed

- Improved error handling and logging for better traceability.

### Fixed

- Fixed encoding issues in text files and improved compatibility with different encodings.

## [1.0.0] - 2024-10-05

### Added

- Initial release with basic image caption generation functionality.
