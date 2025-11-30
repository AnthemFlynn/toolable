# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Toolable** is a Python library that makes any CLI executable a full-featured agent tool without requiring a server. It provides decorators, base classes, and a CLI runner for discovery, validation, execution, streaming, sessions, and LLM sampling callbacks.

## Development Commands

### Setup
```bash
# Install in development mode
pip install -e .

# Install with dev dependencies (once pyproject.toml is updated)
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_decorators.py

# Run with coverage
pytest --cov=toolable --cov-report=term-missing

# Run single test
pytest tests/test_cli.py::test_specific_function -v
```

### Code Quality
```bash
# Run type checking
mypy src/toolable

# Run linting
ruff check src/toolable

# Auto-fix linting issues
ruff check --fix src/toolable
```

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

### Implementation Order

Follow this dependency order when implementing:

1. `errors.py` — foundation for all error handling
2. `response.py` — response envelopes (no dependencies)
3. `input.py` — base class for tool inputs (needs errors)
4. `decorators.py` — metadata registration (needs input)
5. `discovery.py` — schema extraction (needs decorators)
6. Standalone modules: `notifications.py`, `streaming.py`, `session.py`, `sampling.py`
7. `cli.py` — CLI runner (needs everything above)
8. `registry.py` — external tool loading (needs response)
9. `__init__.py` — public API exports

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
- `working_dir: str` → chdir before execution
- `timeout: int` → kill after N seconds
- `dry_run: bool` → validate only, don't execute
- `verbose: bool` → extra detail in response

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

Each module has comprehensive test coverage:

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test full CLI execution paths end-to-end
- **Edge cases**: Validation errors, timeouts, partial failures
- **Streaming/Session**: Bidirectional protocol correctness

Target: >90% code coverage

## Important Implementation Notes

### Schema Generation

The `discovery.py` module extracts schemas from:
1. Explicit `input_model` parameter (Pydantic model)
2. Function signature with type hints
3. Pydantic `Field()` metadata for descriptions/defaults

### Streaming vs Session Modes

- **Streaming**: One-way event emission (progress, logs, artifacts, final result)
- **Session**: Bidirectional communication with `send()`/`yield` protocol

### External Tool Loading

The `ToolRegistry` class discovers external toolable executables by:
1. Running `<path> --discover`
2. Caching manifests
3. Proxying calls via subprocess with JSON I/O

### Sampling Callback

The `sample()` function enables tools to request LLM completions from the caller:
- **stdin mode**: Emit request to stdout, wait for response on stdin
- **HTTP mode**: POST to callback URL, wait for synchronous response
