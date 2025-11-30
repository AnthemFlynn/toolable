# Toolable

Make any CLI executable a full-featured agent tool without requiring a server.

**Toolable** is a Python library that provides decorators, base classes, and a CLI runner to turn your Python functions into agent-callable tools with automatic discovery, validation, execution, streaming, sessions, and LLM sampling callbacks.

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
from toolable import toolable, AgentCLI

@toolable(summary="Add two numbers")
def add(a: int, b: int):
    """Add two numbers and return the sum."""
    return {"sum": a + b}

if __name__ == "__main__":
    AgentCLI(add).run()
```

**Usage:**

```bash
# Human-friendly
python my_tool.py --a 5 --b 3

# Agent-friendly
python my_tool.py '{"a": 5, "b": 3}'

# Discovery
python my_tool.py --discover

# Get schema
python my_tool.py --manifest
```

### Tool with Input Model

```python
from pydantic import Field
from toolable import toolable, AgentCLI, ToolInput

class GreetInput(ToolInput):
    name: str = Field(description="Person's name")
    style: str = Field(default="formal", description="Greeting style: formal or casual")

@toolable(summary="Generate a personalized greeting", input_model=GreetInput)
def greet(input: GreetInput):
    """Generate a greeting based on style."""
    if input.style == "casual":
        return {"message": f"Hey {input.name}!"}
    return {"message": f"Good day, {input.name}."}

if __name__ == "__main__":
    AgentCLI(greet).run()
```

### Error Handling

```python
from toolable import toolable, AgentCLI, ToolError, ErrorCode

@toolable(summary="Divide two numbers")
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
    AgentCLI(divide).run()
```

### Streaming Tool

```python
from toolable import toolable, AgentCLI, stream
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
    AgentCLI(process_items).run()
```

**Usage:**

```bash
python my_tool.py --stream '{"items": ["a", "b", "c"]}'
```

### Session Tool

```python
from toolable import toolable, AgentCLI, session
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
            result = eval(user_input.get("expression", ""))
            yield {"type": "result", "value": result}
        except Exception as e:
            yield {"type": "error", "message": str(e)}

    yield SessionEvent.end()

if __name__ == "__main__":
    AgentCLI(calculator).run()
```

### Multiple Tools

```python
from toolable import toolable, AgentCLI

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
    AgentCLI(create_file).run()
```

### LLM Sampling

Tools can request LLM completions from the caller:

```python
from toolable import toolable, AgentCLI, sample

@toolable(summary="Generate creative content")
def generate_story(topic: str):
    """Generate a story about a topic using LLM sampling."""
    prompt = f"Write a short story about {topic}"
    story = sample(prompt, max_tokens=500, temperature=0.8)
    return {"story": story}

if __name__ == "__main__":
    AgentCLI(generate_story).run()
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
from toolable import toolable, AgentCLI, notify

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
    AgentCLI(process).run()
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

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=toolable --cov-report=term-missing

# Type checking
mypy src/toolable

# Linting
ruff check src/toolable

# Auto-fix linting issues
ruff check --fix src/toolable
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or pull request.
