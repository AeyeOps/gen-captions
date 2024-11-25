# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
