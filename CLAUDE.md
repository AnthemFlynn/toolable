# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Toolable** is a Python library that makes any CLI executable a full-featured agent tool without requiring a server. It provides decorators, base classes, and a CLI runner for discovery, validation, execution, streaming, sessions, and LLM sampling callbacks.

## Development Commands

### Setup
```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install
```

### Testing
```bash
# Run all tests (153 tests, 97% coverage)
pytest

# Run specific test file
pytest tests/test_decorators.py

# Run with coverage report
pytest --cov=toolable --cov-report=term-missing

# Run single test
pytest tests/test_cli.py::test_specific_function -v

# Run tests for specific module coverage
pytest tests/test_cli.py --cov=toolable.cli --cov-report=term-missing
```

### Code Quality
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Run type checking
mypy src/toolable --ignore-missing-imports

# Run linting
ruff check src/toolable tests/

# Auto-fix linting issues
ruff check --fix src/toolable tests/

# Format code
ruff format src/toolable tests/
```

## Project Status

**Current State:**
- **Version**: 0.1.0 (pre-release on dev branch)
- **Test Coverage**: 97% (153 tests)
- **Python Support**: 3.10, 3.11, 3.12, 3.13
- **Platforms**: Linux, macOS, Windows
- **License**: MIT

**Key Metrics:**
- 12 core modules (670 lines of code)
- 8 modules at 100% coverage
- All tests passing on macOS (CI configured for all platforms)

**Infrastructure:**
- CI/CD: `.github/workflows/ci.yml` (tests on all platforms/versions)
- Publishing: `.github/workflows/publish.yml` (automated PyPI releases)
- Pre-commit: `.pre-commit-config.yaml` (ruff, mypy, security checks)
- Community: `CONTRIBUTING.md`, `SECURITY.md`, issue/PR templates

## Important Files for AI Agents

**Development:**
- `CONTRIBUTING.md` - Full development workflow, not duplicated here
- `docs/plans/` - Implementation plans and designs
- `docs/test-coverage-report.md` - Detailed coverage analysis

**Testing:**
- `tests/fixtures/` - Mock tools for registry testing (valid_tool.py, broken_tool.py, etc.)
- Coverage target: 90% minimum, currently at 97%

**Configuration:**
- `pyproject.toml` - Package metadata, dependencies, build config
- `ruff.toml` - Linting rules
- `.pre-commit-config.yaml` - Auto-formatting on commit

## Architecture

### Core Design Principles

1. **Convention over configuration** — sensible defaults, explicit overrides
2. **Pydantic-native** — leverage Field() for schema generation
3. **Dual-mode** — works for humans (--help, --flags) and agents (--manifest, JSON)
4. **Stateless library, stateful tools** — library doesn't manage state, tools can
5. **Progressive disclosure** — discovery → schema → execution

### Module Organization

The library is organized into focused modules with clear dependencies:

```
toolable/
├── __init__.py          # Public API exports
├── errors.py            # ErrorCode enum, ToolError (no dependencies)
├── response.py          # Response envelope helpers (no dependencies)
├── input.py             # ToolInput base class (depends: errors)
├── decorators.py        # @toolable, @resource, @prompt (depends: input)
├── discovery.py         # Schema generation from decorators (depends: decorators)
├── notifications.py     # Progress/logs to stderr (standalone)
├── streaming.py         # Stream type, jsonlines (standalone)
├── session.py           # Bidirectional protocol (standalone)
├── sampling.py          # LLM callback function (standalone)
├── cli.py               # AgentCLI runner (depends: all above)
├── registry.py          # External tool loading (depends: response)
└── py.typed             # PEP 561 marker
```

### Module Dependencies

Understanding module relationships (for modifications):

**Foundation (no dependencies):**
- `errors.py`, `response.py`, `notifications.py`, `streaming.py`, `session.py`, `sampling.py`

**Core (depends on foundation):**
- `input.py` → depends on `errors.py`
- `decorators.py` → depends on `input.py`
- `discovery.py` → depends on `decorators.py`

**Integration (depends on core + foundation):**
- `cli.py` → depends on all above modules
- `registry.py` → depends on `response.py`

**Public API:**
- `__init__.py` → exports from all modules

**When modifying:**
- Changes to foundation modules may require updates throughout
- Changes to `cli.py` are usually isolated
- Always run full test suite after changes to foundation modules

### Key Architectural Patterns

**Response Envelope Pattern**
All tool responses use a consistent envelope with `status` field:
- `success`: operation completed
- `error`: operation failed completely
- `partial`: some operations succeeded, some failed

**Progressive Disclosure**
Tools expose themselves through progressive detail:
1. Discovery (`--discover`): list all capabilities
2. Schema (`<tool> --manifest`): full input/output spec
3. Execution: actual invocation with validation

**Dual Communication Modes**
- **stdout**: Structured JSON responses (for agents)
- **stderr**: Human-readable logs/progress (for monitoring)

**Reserved Field Names in ToolInput**
Subclasses can define these fields to activate special behavior:
- `working_dir: str` → chdir before execution (validated to exist)
- `timeout: int` → kill after N seconds (max 600, cross-platform via signal.alarm or threading.Timer)
- `dry_run: bool` → validate only, don't execute
- `verbose: bool` → extra detail in response

**Timeout Handling (Cross-Platform)**
- Unix/macOS: Uses `signal.alarm()` with SIGALRM handler that raises `ToolError`
- Windows: Uses `threading.Timer` with daemon thread
- Cleanup: `finally` block cancels timer (Windows) or clears alarm (Unix)
- Validation: Must be positive and ≤ 600 seconds
- See `cli.py:26-45` for implementation

**Error Recoverability**
All errors classified as recoverable or not, guiding agent retry behavior:
- Recoverable: `INVALID_INPUT`, `MISSING_PARAM`, `INVALID_PATH`, `NOT_FOUND`, `CONFLICT`, `PRECONDITION`
- Non-recoverable: `TIMEOUT`, `PERMISSION`, `INTERNAL`, `DEPENDENCY`

### CLI Execution Flow

1. Parse argv for global flags (`--discover`, `--tools`, `--help`, etc.)
2. If tool execution: route to specific tool
3. Parse input (JSON via arg, or `--flag value` pairs)
4. Validate input using Pydantic model or function signature
5. Run `pre_validate()` hook for I/O-dependent validation
6. Handle reserved fields (`working_dir`, `timeout`, `dry_run`)
7. Execute tool function
8. Handle response type (streaming generator, session generator, or dict)
9. Emit response envelope to stdout

### Testing Strategy

**Current State: 97% coverage, 153 tests**

Test organization:
- **Unit tests**: Individual functions/classes (`test_errors.py`, `test_response.py`, etc.)
- **Integration tests**: Full CLI execution (`test_integration.py` - 16 tests)
- **Security tests**: URI matching, input validation (`test_security_fixes.py` - 7 tests)
- **Fixtures**: Mock tools in `tests/fixtures/` (valid_tool.py, broken_tool.py, slow_tool.py, etc.)

**Coverage by module:**
- 8 modules at 100%: decorators, errors, notifications, registry, response, session, streaming, + others
- cli.py: 96% (platform-specific code untested)
- All modules >84%

**When adding new features:**
- Write tests first (TDD)
- Maintain 90%+ coverage
- Test error paths, not just happy path
- Add fixtures if testing external interactions
- Run full suite: `pytest tests/ --cov=toolable`

**Common test patterns:**
- Use `monkeypatch` for sys.argv mocking
- Use `capsys` for stdout/stderr capture
- Create fixtures for reusable test tools
- Test both success and error responses

## Important Implementation Notes

### Schema Generation

The `discovery.py` module extracts schemas from:
1. Explicit `input_model` parameter (Pydantic model)
2. Function signature with type hints
3. Pydantic `Field()` metadata for descriptions/defaults

### Streaming vs Session Modes

- **Streaming**: One-way event emission (progress, logs, artifacts, final result)
  - Tools marked `streaming=True` MUST be called with `--stream` flag (enforced in cli.py:255-263)
  - Use `StreamEvent` helpers for progress, logs, artifacts

- **Session**: Bidirectional communication with `send()`/`yield` protocol
  - Tools marked `session_mode=True` MUST be called with `--session` flag (enforced in cli.py:264-272)
  - Generator send() semantics: input N is assigned on yield N+1 (important for testing!)
  - Use `SessionEvent` helpers for start, awaiting, end

### External Tool Loading

The `ToolRegistry` class discovers external toolable executables by:
1. Running `<path> --discover`
2. Caching manifests
3. Proxying calls via subprocess with JSON I/O

### Sampling Callback

The `sample()` function enables tools to request LLM completions from the caller:
- **stdin mode**: Emit request to stdout, wait for response on stdin
- **HTTP mode**: POST to callback URL, wait for synchronous response
