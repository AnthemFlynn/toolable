# Toolable

[![CI](https://github.com/AnthemFlynn/toolable/actions/workflows/ci.yml/badge.svg)](https://github.com/AnthemFlynn/toolable/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](https://github.com/AnthemFlynn/toolable)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/toolable.svg)](https://pypi.org/project/toolable/)

Build CLIs with Typer's great DX, get MCP-like agent features without running a server.

**Toolable** is a fork of [Typer](https://github.com/fastapi/typer) with built-in agent support. Write CLIs with type hints, get discovery, schemas, and JSON I/O automatically - perfect for local agent workflows.

## Features

- **Convention over configuration** - Sensible defaults, explicit overrides
- **Pydantic-native** - Leverage Field() for automatic schema generation
- **Dual-mode** - Works for humans (--help, --flags) and agents (--manifest, JSON)
- **Stateless library, stateful tools** - Library doesn't manage state, tools can
- **Progressive disclosure** - Discovery > Schema > Execution
- **Streaming support** - Real-time progress and logs
- **Bidirectional sessions** - Interactive tool experiences
- **LLM sampling** - Tools can request LLM completions from the caller

## Installation

```bash
pip install toolable
```

## Quick Start

### Simple Tool

```python
from toolable import Toolable

app = Toolable()

@app.command()
def add(a: int, b: int):
    """Add two numbers and return the sum."""
    result = a + b
    return {"sum": result}

if __name__ == "__main__":
    app()
```

**Usage:**

```bash
# Human CLI (standard Typer behavior)
python my_tool.py add 5 3

# Agent discovery
python my_tool.py --discover

# Agent schema
python my_tool.py add --manifest

# Agent JSON execution
python my_tool.py '{"command": "add", "params": {"a": 5, "b": 3}}'
# Returns: {"status": "success", "result": {"sum": 8}}
```

### Multiple Commands

```python
from toolable import Toolable

app = Toolable()

@app.command()
def commit(message: str, amend: bool = False):
    """Commit changes to git."""
    cmd = ['git', 'commit', '-m', message]
    if amend:
        cmd.append('--amend')
    subprocess.run(cmd)
    return {"committed": True, "message": message}

@app.command()
def status():
    """Get git status."""
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    return {"status": result.stdout}

if __name__ == "__main__":
    app()
```

### Error Handling

```python
from toolable import Toolable, ToolError, ErrorCode

app = Toolable()

@app.command()
def divide(a: float, b: float):
    """Divide a by b."""
    if b == 0:
        raise ToolError(
            ErrorCode.INVALID_INPUT,
            "Cannot divide by zero",
            suggestion="Use a non-zero divisor",
            recoverable=True
        )
    return {"result": a / b}

if __name__ == "__main__":
    app()
```

### Streaming Tool

```python
from toolable import Toolable, stream
from toolable.streaming import StreamEvent

@toolable(summary="Process items with progress", streaming=True)
def process_items(items: list[str]) -> stream:
    """Process a list of items with progress updates."""
    total = len(items)
    for i, item in enumerate(items):
        yield StreamEvent.progress(f"Processing {item}...", percent=int((i / total) * 100))
        # ... do work ...

    yield StreamEvent.result({
        "status": "success",
        "result": {"processed": total}
    })

if __name__ == "__main__":
    app = Toolable(); app.command()(process_items); app()
```

**Usage:**

```bash
python my_tool.py --stream '{"items": ["a", "b", "c"]}'
```

### Session Tool

```python
from toolable import Toolable, session
from toolable.session import SessionEvent

@toolable(summary="Interactive calculator", session_mode=True)
def calculator() -> session:
    """Interactive calculator session."""
    yield SessionEvent.start("Calculator started. Enter expressions or 'quit'.")

    while True:
        yield SessionEvent.awaiting(prompt="calc> ")
        user_input = yield

        if user_input.get("action") == "quit":
            break

        try:
            # Use ast.literal_eval for safe expression evaluation
            import ast
            result = ast.literal_eval(user_input.get("expression", ""))
            yield {"type": "result", "value": result}
        except (ValueError, SyntaxError) as e:
            yield {"type": "error", "message": f"Invalid expression: {e}"}

    yield SessionEvent.end()

if __name__ == "__main__":
    app = Toolable(); app.command()(calculator); app()
```

### Multiple Tools

```python
from toolable import Toolable

@toolable(summary="Add two numbers")
def add(a: int, b: int):
    return {"sum": a + b}

@toolable(summary="Multiply two numbers")
def multiply(a: int, b: int):
    return {"product": a * b}

if __name__ == "__main__":
    cli = AgentCLI("mathtools", tools=[add, multiply], version="1.0.0")
    cli.run()
```

**Usage:**

```bash
python mathtools.py --discover
python mathtools.py add '{"a": 5, "b": 3}'
python mathtools.py multiply '{"a": 5, "b": 3}'
```

### Resources

```python
from toolable import resource, AgentCLI

@resource(
    uri_pattern="/files/{file_id}",
    summary="Get file content by ID",
    mime_types=["text/plain"]
)
def get_file(file_id: str):
    """Fetch a file by its ID."""
    # ... load file ...
    return {"content": "File content here", "mime_type": "text/plain"}

if __name__ == "__main__":
    cli = AgentCLI("fileserver")
    cli.register_resource(get_file)
    cli.run()
```

**Usage:**

```bash
python fileserver.py --resource /files/123
```

### Reserved Fields

ToolInput supports reserved field names that activate special behaviors:

```python
from toolable import ToolInput, toolable, AgentCLI

class MyInput(ToolInput):
    name: str
    working_dir: str | None = None  # Change directory before execution
    timeout: int | None = None       # Kill after N seconds
    dry_run: bool = False            # Validate only, don't execute
    verbose: bool = False            # Extra detail in response

@toolable(summary="Create file", input_model=MyInput)
def create_file(input: MyInput):
    if input.verbose:
        return {"message": f"Creating {input.name}", "details": "..."}
    return {"message": f"Created {input.name}"}

if __name__ == "__main__":
    app = Toolable(); app.command()(create_file); app()
```

### LLM Sampling

Tools can request LLM completions from the caller:

```python
from toolable import Toolable, sample

@toolable(summary="Generate creative content")
def generate_story(topic: str):
    """Generate a story about a topic using LLM sampling."""
    prompt = f"Write a short story about {topic}"
    story = sample(prompt, max_tokens=500, temperature=0.8)
    return {"story": story}

if __name__ == "__main__":
    app = Toolable(); app.command()(generate_story); app()
```

**Usage:**

```bash
# Tool will request LLM completion via stdin protocol
python my_tool.py --sample-via stdin '{"topic": "robots"}'

# Or via HTTP callback
python my_tool.py --sample-via http://localhost:8000/sample '{"topic": "robots"}'
```

### External Tool Registry

Discover and call external toolable executables:

```python
from pathlib import Path
from toolable import ToolRegistry

# Load external tools
registry = ToolRegistry([
    Path("./tools/file-tool"),
    Path("./tools/db-tool"),
])

# Discover available tools
summaries = registry.discover()
# {"file-list": "List files", "db-query": "Query database", ...}

# Get schema for a tool
schema = registry.schema("file-list")

# Call a tool
result = registry.call("file-list", {"path": "/tmp"})
```

## Response Envelope

All tools return responses in a consistent envelope format:

**Success:**
```json
{
  "status": "success",
  "result": {"key": "value"}
}
```

**Error:**
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Description",
    "recoverable": true,
    "suggestion": "Try this instead"
  }
}
```

**Partial:**
```json
{
  "status": "partial",
  "result": {"succeeded_items": [...]},
  "summary": {
    "total": 10,
    "succeeded": 7,
    "failed": 3,
    "recoverable_failures": 2
  },
  "errors": [...]
}
```

## Error Codes

Toolable provides standard error codes:

**Recoverable:**
- INVALID_INPUT - Bad input data
- MISSING_PARAM - Required parameter missing
- INVALID_PATH - Path doesn't exist or invalid
- NOT_FOUND - Resource not found
- CONFLICT - Resource conflict
- PRECONDITION - Precondition not met

**Non-recoverable:**
- TIMEOUT - Operation timed out
- PERMISSION - Permission denied
- INTERNAL - Internal error
- DEPENDENCY - External dependency failed

## Notifications

Tools can emit progress and logs to stderr without affecting the stdout response:

```python
from toolable import Toolable, notify

@toolable(summary="Process data")
def process(data: list):
    notify.progress("Starting...", percent=0)

    for i, item in enumerate(data):
        notify.log(f"Processing {item}", level="debug")
        # ... work ...
        notify.progress(f"Progress...", percent=int((i / len(data)) * 100))

    notify.artifact("output.csv", "file:///tmp/output.csv")
    return {"processed": len(data)}

if __name__ == "__main__":
    app = Toolable(); app.command()(process); app()
```

## CLI Flags

**Global flags:**
- --help - Show help
- --discover - List all tools, resources, prompts
- --tools - List tools only
- --resources - List resources only
- --prompts - List prompts only

**Tool flags:**
- <tool> --manifest - Show tool schema
- <tool> --help - Show tool help
- <tool> --validate '{"json": "input"}' - Validate input without executing
- <tool> --stream - Enable streaming mode
- <tool> --session - Enable session mode
- <tool> --sample-via <url|stdin> - Configure LLM sampling transport

## Security Considerations

When building tools with toolable, keep these security best practices in mind:

### Input Validation
- Always validate and sanitize user input before processing
- Use Pydantic models with proper field validation
- Implement `pre_validate()` for I/O-dependent checks
- Never trust external input without validation

### Code Execution
- **Never use `eval()` or `exec()` on user input** - this is a critical security vulnerability
- Use `ast.literal_eval()` for safe literal evaluation
- For expression parsing, use safe libraries like `simpleeval`
- Validate file paths to prevent directory traversal attacks

### Resource Limits
- Set appropriate timeout values (max 600 seconds enforced)
- Validate working directories exist before changing
- Use the `dry_run` field for testing without side effects
- Consider rate limiting for production tools

### Sensitive Data
- Use `to_log_safe()` to redact passwords, tokens, and secrets from logs
- Never log or return sensitive data in error messages
- Use environment variables for configuration secrets
- Avoid hardcoding credentials in tool implementations

### Example: Safe Expression Evaluation
```python
# ❌ UNSAFE - Never do this
result = eval(user_input)

# ✅ SAFE - Use ast.literal_eval for literals
import ast
result = ast.literal_eval(user_input)  # Only allows literals

# ✅ SAFE - Use simpleeval for expressions
from simpleeval import simple_eval
result = simple_eval(user_input, names={"x": 10})
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and workflow
- Testing requirements (90%+ coverage)
- Code style guidelines
- Pull request process

Quick start for contributors:
```bash
pip install -e ".[dev]"  # Install with dev dependencies
pytest tests/            # Run tests (153 tests, 97% coverage)
ruff check src/ tests/   # Check code style
```

## Security

Found a security issue? Please see our [Security Policy](SECURITY.md) for responsible disclosure.

## License

MIT License - see [LICENSE](LICENSE) file for details.
