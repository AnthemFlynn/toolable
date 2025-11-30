# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial implementation of toolable library
- Core decorators: `@toolable`, `@resource`, `@prompt`
- AgentCLI runner with dual-mode support (JSON + CLI flags)
- ToolInput base class with validation hooks
- Response envelope pattern (success/error/partial)
- Structured error handling with ErrorCode enum
- Streaming support for real-time progress
- Bidirectional session protocol
- LLM sampling callbacks (stdin/HTTP)
- External tool registry for discovering executables
- Progress notifications to stderr
- Cross-platform timeout handling
- Comprehensive test suite (153 tests, 97% coverage)
- Complete documentation (README, CLAUDE, CONTRIBUTING, SECURITY)

### Security
- Resource URI pattern matching with proper escaping and anchoring
- Input validation for reserved fields (timeout, working_dir)
- Safe expression evaluation examples (no eval)
- Security documentation and best practices

## [0.1.0] - TBD

Initial release.

### Features
- Convention over configuration design
- Pydantic-native schema generation
- Progressive disclosure (discovery → schema → execution)
- Dual-mode operation (human CLI flags + agent JSON)
- Type-safe with full type hints (py.typed)
- 12 core modules with clear dependency graph

### Supported Platforms
- Python 3.10, 3.11, 3.12, 3.13
- Linux, macOS, Windows

[Unreleased]: https://github.com/AnthemFlynn/toolable/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AnthemFlynn/toolable/releases/tag/v0.1.0
