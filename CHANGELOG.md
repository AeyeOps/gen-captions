# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2025-11-02

### Added

* **Server Auto-Detection**: Automatic detection of LM Studio and Ollama server availability
  - Socket-based connection check on client initialization (2-second timeout)
  - Helpful, backend-specific error messages when servers are not running
  - Clear instructions for starting servers and loading models
  - Mid-processing detection if server goes down during batch operations
  - Zero impact on cloud providers (openai/grok) - check skipped entirely

* **Expanded Ollama Model Support**: 13 recommended vision models (≤8B parameters)
  - **MiniCPM Models** (5 variants): v4.5, o2.6, v4, v2.6, v2.5 - GPT-4o/4V level performance
  - **Qwen Models** (2 variants): 7B, 3B - Flagship vision-language (995K+ pulls)
  - **LLaVA Models** (4 variants): Standard 7B (11.2M pulls), llama3 8B, phi3 3.8B, bakllava 7B
  - **Moondream**: 1.8B ultra-lightweight edge-optimized model
  - All models include full organization/identifier format (e.g., `openbmb/minicpm-v4.5`)
  - Selections based on 2025 community benchmarks and feedback

### Changed

* **Model Parameter Optimization**:
  - Fixed Gemma 3 27B max_tokens: 500 → 256 (aligned with caption generation best practices)
  - Verified all max_tokens values against official model documentation
  - Confirmed temperature=0.1 and top_p defaults optimal for accurate image detection

* **Enhanced Error Handling**:
  - Connection refusal errors now provide actionable troubleshooting steps
  - Different error messages for LM Studio vs Ollama
  - Errors include server URLs and port information from configuration

### Technical

* **New Files**:
  - `tests/unit/test_server_detection.py` - Unit tests for server availability checks (4 tests, all passing)

* **Modified Files**:
  - `gen_captions/openai_generic_client.py`:
    - Added `_verify_local_server_availability()` method for socket-based health checks
    - Added `_raise_server_not_running_error()` for backend-specific error messages
    - Enhanced exception handling in `generate_description()` for mid-processing failures
    - Updated MODEL_CONFIG with 13 new Ollama models
    - Fixed Gemma 3 27B max_tokens value
  - `gen_captions/default.yaml`:
    - Expanded Ollama models section with detailed descriptions
    - Organized by model family (MiniCPM, Qwen, LLaVA, Moondream)
    - Added benchmark information and pull counts
  - `gen_captions/config.py`:
    - Removed unnecessary CURRENT_BACKEND property (simplified)

* **Type Safety**:
  - Fixed mypy type hints for `_build_chat_request()` return type
  - Added type ignore comment for OpenAI SDK dynamic kwargs
  - All new code passes mypy strict checks

### Fixed

* Pre-existing unused import in `duplicate_detector.py` (auto-fixed by ruff)

### Testing

* ✅ All 4 server detection unit tests passing
* ✅ LM Studio connection verified (qwen3-vl-8b)
* ✅ Ollama connection verified (server running)
* ✅ Type checking passes (mypy)
* ✅ Linting clean (ruff)

## [0.5.0] - 2025-11-02

### Added

* **Local Model Support**: Run gen-captions completely offline with local AI servers
  * **LM Studio Integration** (http://localhost:1234/v1)
    - qwen/qwen3-vl-8b - Enhanced visual perception (up to 1M context)
    - qwen/qwen2.5-vl-7b - Dynamic resolution, OCR, chart parsing
    - google/gemma-3-27b - Multimodal (128K context, up to 8K output)
    - mistralai/magistral-small-2509 - Reasoning with vision (128K)
  * **Ollama Integration** (http://localhost:11434/v1)
    - qwen2.5vl:7b - Multimodal with dynamic resolution
    - minicpm-o-2.6:latest - End-to-end multimodal (vision + speech)
  * New model profiles: `lmstudio` and `ollama`
  * No API keys required for local providers (runs completely offline)
  * MODEL_CONFIG entries for all 6 local vision models
* **Concurrent Processing**: Local models support same ThreadPoolExecutor features as cloud APIs
  - Configurable thread pool size for GPU optimization
  - Rate limiting with throttle_submission_rate
  - Exponential backoff retry logic
  - All processing settings apply equally to local/cloud providers

### Changed

* Updated `--model-profile` to accept `lmstudio` and `ollama` in addition to `openai` and `grok`
* Enhanced `config.py` to handle local providers with placeholder API keys
* Updated LLM client factory to recognize local backends (OpenAI-compatible endpoints)
* CLI help text now mentions "vision-capable AI models" and local server support

### Technical

* Modified Files:
  - `gen_captions/default.yaml` - Added lmstudio and ollama backend configurations
  - `gen_captions/config.py` - Added local provider API key handling
  - `gen_captions/llm_client.py` - Extended factory to support lmstudio/ollama
  - `gen_captions/openai_generic_client.py` - Added MODEL_CONFIG for 6 local models
  - `gen_captions/cli.py` - Updated validation and help text
* Both local providers use OpenAI-compatible endpoints (zero client code changes needed)
* Local models automatically get all concurrency and retry features

### Benefits

* ✅ **Privacy**: Images never leave your machine
* ✅ **No API costs**: Free to use after model download
* ✅ **Offline**: Works without internet connection
* ✅ **Fast**: No network latency for inference

## [0.4.0] - 2025-11-02

### Added

* **YAML Configuration System**: Complete migration from environment variables to YAML-based configuration
  * New `default.yaml` bundled with application containing vision model configurations
  * User-customizable local config at `~/.config/gen-captions/config.yaml`
  * Config discovery with search path: env override → user config → project config → working dir
  * Vision model descriptions with recommendations (e.g., "RECOMMENDED: Cost-efficient GPT-5 with excellent vision capabilities")
* **Config Command Group**: New `gen-captions config` subcommands for configuration management
  * `config init` - Create local configuration template
  * `config show [--backend]` - Display current configuration with syntax highlighting
  * `config get <key>` - Retrieve specific config value using dot notation
  * `config set-value <key> <value>` - Update local configuration
  * `config path` - Show configuration file locations
  * `config validate` - Validate configuration against schema
  * `config reset [--force]` - Reset to default configuration
* **Vision Model Updates (November 2025)**
  * Added support for GPT-5 models (gpt-5-mini, gpt-5, gpt-5-nano)
  * Added support for GROK vision models (grok-2-vision-1212, grok-vision-beta)
  * Model-specific quirks now hardcoded in client for cleaner user experience
* **New Configuration Components**
  * `gen_captions/config_manager.py` - YAML file loading, merging, and validation
  * `gen_captions/config_schema.py` - Configuration schema definitions and validation logic
  * `gen_captions/default.yaml` - Default configuration with comprehensive documentation

### Changed

* **Breaking: Configuration Method**
  * Removed `.env` file support and `python-dotenv` dependency
  * Removed `gen-env` command (replaced by `config init`)
  * Removed environment variable configuration for all settings except API keys
  * API keys (`OPENAI_API_KEY`, `GROK_API_KEY`) remain environment-only for security
* **Terminology Update**: `--llm-backend` renamed to `--model-profile` throughout codebase
  * Updated CLI arguments, help text, error messages, and documentation
  * Better terminology that resonates with users selecting vision model configurations
* **Simplified Configuration**
  * Removed internal model quirks from user-facing YAML configuration
  * Model parameters (supports_system_role, max_tokens, etc.) moved to hardcoded dict in `openai_generic_client.py`
  * Configuration now focused on user-relevant settings: model selection, prompts, processing settings
* **Default Models Updated**
  * OpenAI: `gpt-4o-mini` → `gpt-5-mini` (cost-efficient GPT-5 with vision)
  * GROK: `grok-4` → `grok-2-vision-1212` (latest vision model with 32K context)
* **Refactored Configuration Classes**
  * `Config` class now uses `ConfigManager` for YAML loading
  * Removed deprecated environment variable fallbacks
  * Cleaner property accessors for config values
* **Documentation Updates**
  * `CLAUDE.md` - Updated with YAML configuration examples and new workflow
  * `README.md` - Replaced `.env` examples with YAML configuration
  * `AGENTS.md` - Updated command examples with `--model-profile`
* **PyInstaller Build**
  * Updated spec file to bundle `default.yaml` with binary
  * Added PyYAML to hidden imports
  * Removed dotenv from build dependencies

### Removed

* **Backward Compatibility Code**
  * Removed all environment variable fallbacks for configuration settings
  * Removed deprecation warnings system
  * Removed `_load_environment()` function and dotenv discovery logic
  * Removed `gen-env` command entirely
* **Dependencies**
  * Removed `python-dotenv` (no longer needed)
* **Deprecated Environment Variables**
  * `GETCAP_THREAD_POOL` → YAML: `processing.thread_pool`
  * `GETCAP_THROTTLE_SUBMISSION_RATE` → YAML: `processing.throttle_submission_rate`
  * `GETCAP_THROTTLE_RETRIES` → YAML: `processing.throttle_retries`
  * `GETCAP_THROTTLE_BACKOFF_FACTOR` → YAML: `processing.throttle_backoff_factor`
  * `GETCAP_LOG_LEVEL` → YAML: `processing.log_level`
  * `OPENAI_MODEL` / `GROK_MODEL` → YAML: `backends.<profile>.model`
  * `OPENAI_BASE_URL` / `GROK_BASE_URL` → YAML: `backends.<profile>.base_url`

### Fixed

* GROK vision model support - Default changed from non-vision `grok-4` to vision-capable `grok-2-vision-1212`
* Configuration validation with clear error messages for invalid YAML
* Prompt formatting - Removed extra newlines in YAML multi-line strings

## [0.3.0] - 2025-10-28

### Added

* **PyInstaller Binary Build Support**
  * New `gen_captions.spec` for creating standalone executables
  * Makefile `build` target for automated binary creation
  * Binary includes bundled VERSION file and all dependencies
  * Single-file executable output with UPX compression
* **Expanded Model Support**
  * Added model-specific quirk handling for o1-mini, o3-mini
  * Dynamic request parameter building based on model capabilities
  * Support for models with different parameter requirements
* **Enhanced Build System**
  * Updated `pyproject.toml` with hatchling build backend
  * Force-include mechanism for VERSION file in wheel distribution
  * Comprehensive dependency specifications with version pinning

### Changed

* **Project Structure Reorganization**
  * Moved from pants-based build to uv-based dependency management
  * Updated Python requirement to >=3.14
  * Consolidated dependencies in pyproject.toml
* **Improved Error Handling**
  * Better API key validation and error messages
  * Graceful handling of missing configuration
  * Detailed logging for model selection and parameters
* **Documentation**
  * Updated README with binary build instructions
  * Added CLAUDE.md with development workflow documentation
  * Improved inline code documentation

### Fixed

* Model parameter compatibility issues with different OpenAI models
* VERSION file bundling in PyInstaller binary
* Configuration defaults for missing environment variables

## [0.2.3] - 2025-02-20

### Added

* **Contributor Guide**: Added `AGENTS.md` describing project layout, tooling, and contribution conventions for agents and maintainers.
* **Feature Step Placeholders**: Added lightweight pytest-compatible guards in `tests/features/steps/*.py` so Pants can collect the Behave step modules without errors.

### Changed

* **CLI Defaults & UX**
  * `gen_captions/cli.py` now ensures the caption output directory exists before writing files and surfaces top-level help when no subcommand is provided.
  * `gen_captions/config.py` supplies default OpenAI model (`gpt-4o-mini`) and base URL fallbacks, while `gen_captions/openai_generic_client.py` logs when those defaults are used and warns if the API key is missing.
  * `gen_captions/logger_config.py` gracefully degrades when the optional queue helper is unavailable.
  * `gen_captions/image_processor.py` reuses the Rich progress helper import path shared with the encoding fixer.
* **Documentation Updates**
  * `README.md` now documents the new environment fallbacks, the `GEN_CAPTIONS_ENV_FILE` override, and clarifies optional OpenAI settings.
  * `AGENTS.md` references the default model/base URL behaviour.
* **Tests**
  * Updated unit tests to patch the revised imports (`tests/unit/test_image_processor.py`) and to assert UTF-8 round-tripping in `tests/unit/test_encoding_fixer.py`.
  * `tests/unit/test_openai_api.py` now stubs `encode_image` so the OpenAI client mock no longer hits the filesystem.

### Dependency Updates

* Added `rich` to `requirements/requirements.txt` and regenerated `gen_captions/lockfile.lock`, which pulled in upstream upgrades (e.g. `openai 2.5.0`, `black 25.9.0`, `torch 2.9.0`, `transformers 4.57.1`, and related CUDA libraries).

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
