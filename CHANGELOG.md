# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
