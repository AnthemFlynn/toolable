# Fork Typer to Toolable Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fork Typer, rename to Toolable, add agent features (discovery, schemas, JSON I/O, resources) directly into the framework

**Architecture:** Fork Typer's proven CLI foundation (~5K LOC), rename Typer→Toolable, intercept `__call__` to detect agent flags (--discover, --manifest, JSON input), reuse response/error envelopes from current toolable, maintain full Typer API compatibility

**Tech Stack:** Typer (forked), Click (dependency), Pydantic (current), ast-grep (refactoring), GitHub CLI (repo operations)

---

## Phase 1: Fork and Integrate Typer

### Task 1: Fork Typer Repository

**Files:**
- Create: `/tmp/typer-fork/` (temporary location)
- Reference: Current `/Users/dblspeak/projects/toolable/`

**Step 1: Clone Typer into temp location**

Run:
```bash
cd /tmp
git clone https://github.com/fastapi/typer.git typer-fork
cd typer-fork
git log --oneline -5
```

Expected: Typer repository cloned, see recent commits

**Step 2: Examine Typer structure**

Run:
```bash
ls -la typer/
cat pyproject.toml | grep -A 10 "\[project\]"
cat typer/__init__.py
```

Expected: Understand Typer's file structure and entry points

**Step 3: Create integration branch in toolable**

Run:
```bash
cd /Users/dblspeak/projects/toolable
git checkout dev
git checkout -b refactor/integrate-typer-fork
```

Expected: New branch created from dev

**Step 4: Document current toolable structure to preserve**

Run:
```bash
ls -la src/toolable/
echo "Files to keep:"
echo "- errors.py"
echo "- response.py"
echo "- streaming.py"
echo "- session.py"
echo "- sampling.py"
echo "- notifications.py"
```

Expected: Clear understanding of what we're keeping

**Step 5: Commit checkpoint**

Run:
```bash
git commit --allow-empty -m "refactor: start Typer integration - checkpoint"
git push -u origin refactor/integrate-typer-fork
```

Expected: Branch created on remote

---

### Task 2: Copy Typer Source into Toolable

**Files:**
- Copy: `/tmp/typer-fork/typer/*` → `/Users/dblspeak/projects/toolable/src/toolable/`
- Preserve: `src/toolable/errors.py`, `response.py`, etc.

**Step 1: Backup current toolable modules**

Run:
```bash
cd /Users/dblspeak/projects/toolable
mkdir -p .backup/toolable-original
cp src/toolable/*.py .backup/toolable-original/
ls -la .backup/toolable-original/
```

Expected: Current modules backed up

**Step 2: Copy Typer source files**

Run:
```bash
# Copy all Typer Python files except __pycache__
cp -r /tmp/typer-fork/typer/*.py src/toolable/
ls -la src/toolable/
```

Expected: Typer source files now in src/toolable/ (main.py, core.py, models.py, etc.)

**Step 3: Restore our essential modules**

Run:
```bash
# Restore files we want to keep
cp .backup/toolable-original/errors.py src/toolable/
cp .backup/toolable-original/response.py src/toolable/
cp .backup/toolable-original/streaming.py src/toolable/
cp .backup/toolable-original/session.py src/toolable/
cp .backup/toolable-original/sampling.py src/toolable/
cp .backup/toolable-original/notifications.py src/toolable/
```

Expected: Our custom modules preserved alongside Typer files

**Step 4: Remove old files we're replacing**

Run:
```bash
rm -f src/toolable/cli.py  # Replaced by Typer's main.py
rm -f src/toolable/decorators.py  # Typer has its own
rm -f src/toolable/discovery.py  # Will use Typer's type system
rm -f src/toolable/input.py  # Typer handles params differently
rm -f src/toolable/registry.py  # Keep for later integration
```

Expected: Old framework code removed

**Step 5: Update __init__.py to export Typer's Typer class**

Create `src/toolable/__init__.py`:

```python
# Import Typer's main class
from toolable.main import Typer

# Keep our response/error system
from toolable.errors import ErrorCode, ToolError
from toolable.response import Response
from toolable.streaming import StreamEvent, stream
from toolable.session import SessionEvent, session
from toolable.sampling import sample
from toolable.notifications import notify

# Re-export Typer's utilities
from toolable.params import Argument, Option
from toolable.models import FileText, FileTextWrite, FileBinaryRead, FileBinaryWrite

__all__ = [
    # Main class (still called Typer for now)
    "Typer",
    # Typer utilities
    "Argument",
    "Option",
    "FileText",
    "FileTextWrite",
    "FileBinaryRead",
    "FileBinaryWrite",
    # Our additions
    "ErrorCode",
    "ToolError",
    "Response",
    "StreamEvent",
    "stream",
    "SessionEvent",
    "session",
    "sample",
    "notify",
]

__version__ = "0.2.0"
```

**Step 6: Test that basic Typer functionality works**

Run:
```bash
python -c "
from toolable import Typer

app = Typer()

@app.command()
def hello(name: str):
    print(f'Hello {name}')

# Test it can be created
print('Success: Typer imported and works')
"
```

Expected: No errors, prints "Success: Typer imported and works"

**Step 7: Commit Typer integration**

Run:
```bash
git add src/toolable/
git commit -m "refactor: integrate Typer source as foundation

- Copy Typer source files to src/toolable/
- Preserve response.py, errors.py, streaming.py, session.py, sampling.py, notifications.py
- Remove old cli.py, decorators.py, discovery.py, input.py
- Update __init__.py to export Typer + our additions
- Typer class unchanged, agent features to be added next"
```

Expected: Commit created with Typer integration

---

### Task 3: Rename Typer Class to Toolable

**Files:**
- Modify: `src/toolable/main.py` (rename class Typer → Toolable)
- Modify: `src/toolable/__init__.py` (export Toolable)
- Use: ast-grep for refactoring

**Step 1: Rename Typer class to Toolable using ast-grep**

Run:
```bash
cd /Users/dblspeak/projects/toolable

# Find all "class Typer" declarations
ast-grep --pattern 'class Typer:' src/toolable/main.py
```

Expected: Shows line with "class Typer:"

**Step 2: Replace class name**

Edit `src/toolable/main.py`:
- Find: `class Typer:`
- Replace: `class Toolable:`

**Step 3: Update type references in main.py**

Run:
```bash
# Find all Typer type references
grep -n "Typer\[" src/toolable/main.py | head -10
grep -n "-> Typer" src/toolable/main.py | head -10
grep -n "typer_instance: Typer" src/toolable/main.py
```

Expected: List of lines with type annotations

**Step 4: Replace type references**

Edit `src/toolable/main.py`:
- Find all: `typer_instance: Typer` → Replace: `toolable_instance: Toolable`
- Find all: `def get_group(typer_instance: Typer)` → Replace: `def get_group(toolable_instance: Toolable)`
- Find all: `def get_command(typer_instance: Typer)` → Replace: `def get_command(toolable_instance: Toolable)`

**Step 5: Update internal references**

Edit `src/toolable/main.py`:
- Find all: `typer_instance.` → Replace: `toolable_instance.`
- Find all: `TyperInfo(typer_instance)` → Replace: `TyperInfo(toolable_instance)`

**Step 6: Update __init__.py exports**

Edit `src/toolable/__init__.py`:
```python
from toolable.main import Toolable  # Changed from Typer

__all__ = [
    "Toolable",  # Changed from "Typer"
    # ... rest unchanged
]
```

**Step 7: Test renamed class works**

Run:
```bash
python -c "
from toolable import Toolable

app = Toolable()

@app.command()
def test():
    print('Works')

print('Toolable class imported successfully')
"
```

Expected: "Toolable class imported successfully"

**Step 8: Commit rename**

Run:
```bash
git add src/toolable/main.py src/toolable/__init__.py
git commit -m "refactor: rename Typer class to Toolable

- Rename class Typer → Toolable in main.py
- Update all type annotations (typer_instance → toolable_instance)
- Update __init__.py exports
- Preserves all functionality, just renamed"
```

Expected: Commit created

---

### Task 4: Add Agent Flag Detection to __call__

**Files:**
- Modify: `src/toolable/main.py` (Toolable.__call__ method around line 308)

**Step 1: Locate __call__ method**

Run:
```bash
grep -n "def __call__" src/toolable/main.py
```

Expected: Shows line number (around 308)

**Step 2: Read current __call__ implementation**

View `src/toolable/main.py` around line 308:
```python
def __call__(self, *args: Any, **kwargs: Any) -> Any:
    if sys.excepthook != except_hook:
        sys.excepthook = except_hook
    try:
        return get_command(self)(*args, **kwargs)
    except Exception as e:
        # ... error handling
```

**Step 3: Add agent flag detection before normal execution**

Edit `src/toolable/main.py`, modify `__call__` to:

```python
def __call__(self, *args: Any, **kwargs: Any) -> Any:
    # Check for agent flags BEFORE normal Typer execution
    if len(sys.argv) > 1:
        if sys.argv[1] == "--discover":
            return self._agent_discover()

        # Check if first arg looks like JSON input (starts with {)
        if sys.argv[1].startswith("{"):
            return self._agent_execute_json(sys.argv[1])

        # Check for --manifest on specific command
        if len(sys.argv) > 2 and sys.argv[2] == "--manifest":
            command_name = sys.argv[1]
            return self._agent_manifest(command_name)

    # Normal Typer execution unchanged
    if sys.excepthook != except_hook:
        sys.excepthook = except_hook
    try:
        return get_command(self)(*args, **kwargs)
    except Exception as e:
        setattr(
            e,
            _typer_developer_exception_attr_name,
            DeveloperExceptionConfig(
                pretty_exceptions_enable=self.pretty_exceptions_enable,
                pretty_exceptions_show_locals=self.pretty_exceptions_show_locals,
                pretty_exceptions_short=self.pretty_exceptions_short,
            ),
        )
        raise e
```

**Step 4: Add stub methods**

Add to `Toolable` class in `src/toolable/main.py`:

```python
def _agent_discover(self) -> None:
    """Handle --discover flag for agent tool discovery."""
    # TODO: Implement discovery
    import json
    from toolable.response import Response

    result = {
        "name": self.info.name or "tool",
        "version": "0.2.0",
        "tools": [],
        "resources": [],
        "prompts": []
    }
    print(json.dumps(result))

def _agent_manifest(self, command_name: str) -> None:
    """Handle --manifest flag for command schema."""
    # TODO: Implement manifest
    import json
    from toolable.response import Response

    print(json.dumps({"command": command_name, "schema": {}}))

def _agent_execute_json(self, json_input: str) -> None:
    """Handle JSON input execution."""
    # TODO: Implement JSON execution
    import json
    from toolable.response import Response

    print(json.dumps(Response.error("NOT_IMPLEMENTED", "JSON execution not yet implemented")))
```

**Step 5: Test agent flag detection**

Run:
```bash
python -c "
import sys
from toolable import Toolable

app = Toolable()

@app.command()
def test():
    print('Normal command')

# Simulate --discover
sys.argv = ['app.py', '--discover']
app()
" 2>&1
```

Expected: Prints JSON discovery output (even if empty)

**Step 6: Commit agent flag detection**

Run:
```bash
git add src/toolable/main.py
git commit -m "feat: add agent flag detection to Toolable.__call__

- Intercept --discover, --manifest, JSON input before normal Typer execution
- Add stub _agent_discover, _agent_manifest, _agent_execute_json methods
- Normal Typer CLI unchanged
- Stubs return placeholder JSON for now"
```

Expected: Commit created

---

### Task 5: Implement Discovery (_agent_discover)

**Files:**
- Modify: `src/toolable/main.py` (_agent_discover method)
- Test: Create `tests/test_agent_features.py`

**Step 1: Write test for discovery**

Create `tests/test_agent_features.py`:

```python
import json
import sys
from io import StringIO

from toolable import Toolable


def test_discover_lists_commands(monkeypatch, capsys):
    """Test --discover flag lists all registered commands."""
    app = Toolable()

    @app.command()
    def hello(name: str):
        """Say hello."""
        print(f"Hello {name}")

    @app.command()
    def goodbye(name: str):
        """Say goodbye."""
        print(f"Goodbye {name}")

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert "tools" in result
    assert len(result["tools"]) == 2
    assert any(t["name"] == "hello" for t in result["tools"])
    assert any(t["name"] == "goodbye" for t in result["tools"])


def test_discover_includes_command_summaries(monkeypatch, capsys):
    """Test discovery includes command summaries."""
    app = Toolable()

    @app.command()
    def hello(name: str):
        """Say hello to someone."""
        print(f"Hello {name}")

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    hello_tool = next(t for t in result["tools"] if t["name"] == "hello")
    assert "Say hello" in hello_tool["summary"]
```

**Step 2: Run tests to see them fail**

Run:
```bash
pytest tests/test_agent_features.py::test_discover_lists_commands -v
pytest tests/test_agent_features.py::test_discover_includes_command_summaries -v
```

Expected: FAIL - stubs return empty tools list

**Step 3: Implement discovery**

Edit `src/toolable/main.py`, replace `_agent_discover` method:

```python
def _agent_discover(self) -> None:
    """Handle --discover flag for agent tool discovery."""
    import json

    tools = []

    # Extract registered commands
    for command_info in self.registered_commands:
        # Get docstring for summary
        callback = command_info.callback
        doc = inspect.getdoc(callback) or ""
        summary = doc.split("\n")[0] if doc else ""

        tools.append({
            "name": command_info.name or callback.__name__,
            "summary": summary,
            "streaming": False,  # TODO: detect from decorators
            "session_mode": False,
        })

    result = {
        "name": self.info.name or "tool",
        "version": "0.2.0",
        "tools": tools,
        "resources": [],  # TODO: implement resources
        "prompts": [],    # TODO: implement prompts
    }

    print(json.dumps(result, indent=2))
```

**Step 4: Run tests to see them pass**

Run:
```bash
pytest tests/test_agent_features.py::test_discover_lists_commands -v
pytest tests/test_agent_features.py::test_discover_includes_command_summaries -v
```

Expected: PASS - discovery now returns registered commands

**Step 5: Commit discovery implementation**

Run:
```bash
git add src/toolable/main.py tests/test_agent_features.py
git commit -m "feat: implement --discover flag

- Extract registered commands from self.registered_commands
- Return JSON with tool names and summaries
- Use docstring first line as summary
- Tests verify command discovery works"
```

Expected: Commit created

---

### Task 6: Implement Schema Generation (_agent_manifest)

**Files:**
- Modify: `src/toolable/main.py` (_agent_manifest method)
- Modify: `tests/test_agent_features.py`

**Step 1: Write test for manifest**

Add to `tests/test_agent_features.py`:

```python
def test_manifest_returns_command_schema(monkeypatch, capsys):
    """Test --manifest flag returns command schema."""
    from pydantic import Field

    app = Toolable()

    @app.command()
    def commit(
        message: str,
        files: list[str] = None,
        amend: bool = False,
    ):
        """Commit changes to git."""
        pass

    monkeypatch.setattr(sys, "argv", ["app.py", "commit", "--manifest"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["name"] == "commit"
    assert "schema" in result
    assert "properties" in result["schema"]
    assert "message" in result["schema"]["properties"]
    assert "files" in result["schema"]["properties"]
    assert "amend" in result["schema"]["properties"]
    assert result["schema"]["properties"]["message"]["type"] == "string"
```

**Step 2: Run test to see it fail**

Run:
```bash
pytest tests/test_agent_features.py::test_manifest_returns_command_schema -v
```

Expected: FAIL - stub returns empty schema

**Step 3: Implement manifest generation**

Edit `src/toolable/main.py`, replace `_agent_manifest`:

```python
def _agent_manifest(self, command_name: str) -> None:
    """Handle --manifest flag for command schema."""
    import json
    from typing import get_type_hints

    # Find the command
    command_info = None
    for cmd in self.registered_commands:
        if cmd.name == command_name or cmd.callback.__name__ == command_name:
            command_info = cmd
            break

    if not command_info:
        from toolable.response import Response
        print(json.dumps(Response.error("NOT_FOUND", f"Command '{command_name}' not found")))
        return

    # Extract schema from function signature
    callback = command_info.callback
    type_hints = get_type_hints(callback)
    sig = inspect.signature(callback)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ("ctx", "self", "cls"):
            continue

        param_type = type_hints.get(param_name, str)
        json_type = _python_type_to_json(param_type)

        prop = {"type": json_type}

        # Check if required (no default)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default

        properties[param_name] = prop

    schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required

    result = {
        "name": command_name,
        "summary": (inspect.getdoc(callback) or "").split("\n")[0],
        "description": inspect.getdoc(callback) or "",
        "schema": schema,
    }

    print(json.dumps(result, indent=2))


def _python_type_to_json(py_type) -> str:
    """Map Python types to JSON schema types."""
    origin = getattr(py_type, "__origin__", None)

    if origin is list:
        return "array"
    if origin is dict:
        return "object"

    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(py_type, "string")
```

**Step 4: Run test**

Run:
```bash
pytest tests/test_agent_features.py::test_manifest_returns_command_schema -v
```

Expected: PASS - manifest generated from type hints

**Step 5: Commit manifest implementation**

Run:
```bash
git add src/toolable/main.py tests/test_agent_features.py
git commit -m "feat: implement --manifest flag for schema generation

- Extract command by name from registered_commands
- Generate JSON schema from function signature and type hints
- Map Python types to JSON schema types
- Return command name, summary, description, schema
- Test verifies schema generation works"
```

Expected: Commit created

---

### Task 7: Implement JSON Input Execution (_agent_execute_json)

**Files:**
- Modify: `src/toolable/main.py` (_agent_execute_json method)
- Modify: `tests/test_agent_features.py`

**Step 1: Write test for JSON execution**

Add to `tests/test_agent_features.py`:

```python
def test_json_input_executes_command(monkeypatch, capsys):
    """Test JSON input executes command."""
    app = Toolable()

    @app.command()
    def add(a: int, b: int):
        """Add two numbers."""
        result = a + b
        # Return dict for agent mode
        return {"sum": result}

    monkeypatch.setattr(sys, "argv", ["app.py", '{"command": "add", "params": {"a": 5, "b": 3}}'])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["status"] == "success"
    assert result["result"]["sum"] == 8
```

**Step 2: Run test to see it fail**

Run:
```bash
pytest tests/test_agent_features.py::test_json_input_executes_command -v
```

Expected: FAIL - stub returns NOT_IMPLEMENTED

**Step 3: Implement JSON execution**

Edit `src/toolable/main.py`, replace `_agent_execute_json`:

```python
def _agent_execute_json(self, json_input: str) -> None:
    """Handle JSON input execution."""
    import json
    from toolable.response import Response
    from toolable.errors import ToolError, ErrorCode

    try:
        # Parse JSON input
        data = json.loads(json_input)
        command_name = data.get("command")
        params = data.get("params", {})

        if not command_name:
            print(json.dumps(Response.error(
                "INVALID_INPUT",
                "JSON must include 'command' field",
                suggestion='Use format: {"command": "name", "params": {...}}'
            )))
            return

        # Find command
        command_info = None
        for cmd in self.registered_commands:
            if cmd.name == command_name or cmd.callback.__name__ == command_name:
                command_info = cmd
                break

        if not command_info:
            print(json.dumps(Response.error(
                "NOT_FOUND",
                f"Command '{command_name}' not found",
                recoverable=True
            )))
            return

        # Execute command with params
        try:
            result = command_info.callback(**params)

            # Wrap result in envelope if not already
            if isinstance(result, dict) and "status" in result:
                print(json.dumps(result))
            else:
                print(json.dumps(Response.success(result if isinstance(result, dict) else {"result": result})))

        except ToolError as e:
            print(json.dumps(e.to_response()))
        except Exception as e:
            print(json.dumps(Response.error(
                "INTERNAL",
                str(e),
                recoverable=False
            )))

    except json.JSONDecodeError as e:
        print(json.dumps(Response.error(
            "INVALID_INPUT",
            f"Invalid JSON: {e}",
            recoverable=True
        )))
```

**Step 4: Run test**

Run:
```bash
pytest tests/test_agent_features.py::test_json_input_executes_command -v
```

Expected: PASS - JSON execution works

**Step 5: Commit JSON execution**

Run:
```bash
git add src/toolable/main.py tests/test_agent_features.py
git commit -m "feat: implement JSON input execution

- Parse JSON with command name and params
- Find and execute registered command
- Wrap result in Response envelope
- Handle errors with proper error codes
- Test verifies JSON execution works"
```

Expected: Commit created

---

### Task 8: Add @resource Decorator Support

**Files:**
- Create: `src/toolable/decorators.py` (lightweight, just for resources/prompts)
- Modify: `src/toolable/main.py` (add resource support)
- Modify: `src/toolable/__init__.py`

**Step 1: Create lightweight decorators module**

Create `src/toolable/decorators.py`:

```python
"""Decorators for resources and prompts (tools use @app.command)."""

from functools import wraps
from typing import Callable

_RESOURCE_REGISTRY: dict[Callable, dict] = {}
_PROMPT_REGISTRY: dict[Callable, dict] = {}


def resource(
    uri_pattern: str,
    summary: str,
    mime_types: list[str] | None = None,
):
    """Decorator to mark a function as a resource provider."""
    def decorator(fn: Callable) -> Callable:
        _RESOURCE_REGISTRY[fn] = {
            "uri_pattern": uri_pattern,
            "summary": summary,
            "mime_types": mime_types or [],
        }

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper._resource_meta = _RESOURCE_REGISTRY[fn]
        return wrapper

    return decorator


def prompt(
    summary: str,
    arguments: dict[str, str],
):
    """Decorator to mark a function as a prompt template."""
    def decorator(fn: Callable) -> Callable:
        _PROMPT_REGISTRY[fn] = {
            "summary": summary,
            "arguments": arguments,
        }

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper._prompt_meta = _PROMPT_REGISTRY[fn]
        return wrapper

    return decorator


def get_resource_meta(fn: Callable) -> dict | None:
    return getattr(fn, "_resource_meta", None)


def get_prompt_meta(fn: Callable) -> dict | None:
    return getattr(fn, "_prompt_meta", None)
```

**Step 2: Add resource registration to Toolable**

Edit `src/toolable/main.py`, add to `Toolable.__init__`:

```python
def __init__(
    self,
    # ... existing params ...
):
    # ... existing init code ...

    # Add resource/prompt storage
    self._resources: dict[str, Callable] = {}
    self._prompts: dict[str, Callable] = {}
```

Add methods to `Toolable` class:

```python
def resource(self, uri_pattern: str, summary: str, mime_types: list[str] | None = None):
    """Register a resource provider."""
    from toolable.decorators import resource as resource_decorator
    return resource_decorator(uri_pattern, summary, mime_types)

def prompt_template(self, summary: str, arguments: dict[str, str]):
    """Register a prompt template."""
    from toolable.decorators import prompt as prompt_decorator
    return prompt_decorator(summary, arguments)

def register_resource(self, fn: Callable) -> None:
    """Register a resource function."""
    from toolable.decorators import get_resource_meta
    meta = get_resource_meta(fn)
    if not meta:
        raise ValueError(f"{fn.__name__} is not decorated with @resource")
    self._resources[meta["uri_pattern"]] = fn

def register_prompt(self, fn: Callable) -> None:
    """Register a prompt function."""
    from toolable.decorators import get_prompt_meta
    meta = get_prompt_meta(fn)
    if not meta:
        raise ValueError(f"{fn.__name__} is not decorated with @prompt")
    self._prompts[fn.__name__] = fn
```

**Step 3: Update discovery to include resources/prompts**

Edit `src/toolable/main.py`, update `_agent_discover`:

```python
def _agent_discover(self) -> None:
    """Handle --discover flag for agent tool discovery."""
    import json
    from toolable.decorators import get_resource_meta, get_prompt_meta

    # ... tools extraction (unchanged) ...

    # Extract resources
    resources = []
    for uri_pattern, fn in self._resources.items():
        meta = get_resource_meta(fn)
        if meta:
            resources.append({
                "uri_pattern": uri_pattern,
                "summary": meta["summary"],
                "mime_types": meta.get("mime_types", []),
            })

    # Extract prompts
    prompts = []
    for name, fn in self._prompts.items():
        meta = get_prompt_meta(fn)
        if meta:
            prompts.append({
                "name": name,
                "summary": meta["summary"],
                "arguments": meta.get("arguments", {}),
            })

    result = {
        "name": self.info.name or "tool",
        "version": "0.2.0",
        "tools": tools,
        "resources": resources,
        "prompts": prompts,
    }

    print(json.dumps(result, indent=2))
```

**Step 4: Test resources**

Add to `tests/test_agent_features.py`:

```python
def test_discover_includes_resources(monkeypatch, capsys):
    """Test discovery includes resources."""
    app = Toolable()

    @app.resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id, "content": "..."}

    app.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert len(result["resources"]) == 1
    assert result["resources"][0]["uri_pattern"] == "/files/{id}"
```

**Step 5: Run test**

Run:
```bash
pytest tests/test_agent_features.py::test_discover_includes_resources -v
```

Expected: PASS

**Step 6: Commit resource support**

Run:
```bash
git add src/toolable/decorators.py src/toolable/main.py src/toolable/__init__.py tests/test_agent_features.py
git commit -m "feat: add @resource and @prompt decorator support

- Create lightweight decorators.py for resources/prompts
- Add resource() and prompt_template() methods to Toolable
- Add register_resource/register_prompt methods
- Update discovery to include resources and prompts
- Tests verify resource discovery works"
```

Expected: Commit created

---

### Task 9: Wire in Response Envelopes

**Files:**
- Modify: `src/toolable/main.py` (use Response envelopes everywhere)
- Already have: `src/toolable/response.py`, `src/toolable/errors.py`

**Step 1: Update imports in main.py**

Edit `src/toolable/main.py`, add to imports:

```python
from toolable.response import Response
from toolable.errors import ToolError, ErrorCode
```

**Step 2: Verify all agent methods use Response**

Check that `_agent_discover`, `_agent_manifest`, `_agent_execute_json` all use:
- `Response.success(result)` for success
- `Response.error(code, message)` for errors
- `ToolError` for exceptions

**Step 3: Add response envelope to normal command execution**

This is optional - but we could wrap normal Typer output too.

For now, just ensure agent mode uses envelopes (already done).

**Step 4: Test error handling**

Add to `tests/test_agent_features.py`:

```python
def test_json_execution_handles_tool_error(monkeypatch, capsys):
    """Test JSON execution properly handles ToolError."""
    from toolable.errors import ToolError, ErrorCode

    app = Toolable()

    @app.command()
    def divide(a: float, b: float):
        """Divide a by b."""
        if b == 0:
            raise ToolError(ErrorCode.INVALID_INPUT, "Cannot divide by zero")
        return {"result": a / b}

    monkeypatch.setattr(sys, "argv", ["app.py", '{"command": "divide", "params": {"a": 10, "b": 0}}'])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
    assert "divide by zero" in result["error"]["message"]
```

**Step 5: Run test**

Run:
```bash
pytest tests/test_agent_features.py::test_json_execution_handles_tool_error -v
```

Expected: PASS (already implemented in _agent_execute_json)

**Step 6: Commit**

Run:
```bash
git add tests/test_agent_features.py
git commit -m "test: verify response envelope integration

- Test ToolError handling in JSON execution
- Verify error codes and messages in response
- Response envelopes working correctly"
```

Expected: Commit created

---

### Task 10: Update pyproject.toml and Documentation

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Step 1: Update pyproject.toml dependencies**

Edit `pyproject.toml`:

```toml
[project]
name = "toolable"
version = "0.2.0"
description = "Typer + MCP-like features for agent-callable CLIs without a server"
# ... existing metadata ...

dependencies = [
    "click>=8.0.0",
    "typing-extensions>=3.7.4.3",
    "pydantic>=2.0",
]

[project.optional-dependencies]
standard = [
    "shellingham>=1.3.0",
    "rich>=10.11.0",
]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff",
    "mypy",
    "pre-commit",
]
```

**Step 2: Update README.md introduction**

Edit `README.md`, update first section:

```markdown
# Toolable

[![CI](https://github.com/AnthemFlynn/toolable/actions/workflows/ci.yml/badge.svg)](...)
...

Build CLIs with Typer's great DX, get MCP-like agent features without running a server.

**Toolable** is a fork of [Typer](https://github.com/fastapi/typer) with built-in agent support. Write your CLI with type hints, get discovery, schemas, and JSON I/O automatically.

## Why Toolable?

- **Based on Typer** - All of Typer's features (type hints, rich output, completion)
- **Agent-ready** - Discovery, schemas, JSON I/O built-in
- **No server** - Direct CLI calls (faster than HTTP/stdio MCP servers)
- **Dual-mode** - Same CLI for humans (`--help` flags) and agents (`--discover`, JSON)
- **MCP-like** - Tools, resources, prompts (without the server overhead)

## Quick Start

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
    return {"status": "committed", "message": message}

if __name__ == "__main__":
    app()  # Handles both human CLI and agent calls
```

**Human usage (unchanged from Typer):**
```bash
python git-tool.py commit --message "fix bug" --amend
```

**Agent usage (NEW):**
```bash
# Discovery
python git-tool.py --discover

# Get schema
python git-tool.py commit --manifest

# Execute with JSON
python git-tool.py '{"command": "commit", "params": {"message": "fix bug"}}'
```
```

**Step 3: Update CLAUDE.md**

Edit `CLAUDE.md`, add to Project Overview:

```markdown
## Project Overview

**Toolable** is a fork of [Typer](https://github.com/fastapi/typer) with built-in agent support.

**What we forked:**
- Typer 0.15.1 (latest as of Nov 2024)
- Full Typer API compatibility maintained
- Added agent features on top

**Key additions:**
- Agent flag detection in `Toolable.__call__`
- `--discover` flag for tool/resource/prompt discovery
- `--manifest` flag for command schema generation
- JSON input mode: `'{"command": "name", "params": {...}}'`
- Response envelope pattern for structured output
- @resource and @prompt decorators (MCP-like)

**Typer baseline:**
- `typer/main.py` - Core Toolable class (forked from Typer)
- `typer/core.py` - Click integration (unchanged)
- `typer/models.py` - Type models (unchanged)
- Full Typer documentation applies: https://typer.tiangolo.com/

**Our additions:**
- `toolable/response.py` - Response envelopes
- `toolable/errors.py` - Error codes
- `toolable/decorators.py` - @resource, @prompt
- `toolable/streaming.py` - Streaming support
- `toolable/session.py` - Session support
- `toolable/sampling.py` - LLM sampling
- `toolable/notifications.py` - Progress notifications
```

**Step 4: Commit documentation updates**

Run:
```bash
git add pyproject.toml README.md CLAUDE.md
git commit -m "docs: update for Typer fork architecture

- Update pyproject.toml version to 0.2.0
- Add Typer dependencies (click, typing-extensions)
- Update README to explain Typer fork approach
- Update CLAUDE.md with fork details and preserved modules
- Clarify that toolable = Typer + agent features"
```

Expected: Commit created

---

### Task 11: Add Typer's Test Suite

**Files:**
- Copy: `/tmp/typer-fork/tests/` → `/Users/dblspeak/projects/toolable/tests/typer_tests/`

**Step 1: Copy Typer's tests**

Run:
```bash
mkdir -p tests/typer_tests
cp -r /tmp/typer-fork/tests/* tests/typer_tests/
ls tests/typer_tests/ | head -10
```

Expected: Typer's test suite copied

**Step 2: Update test imports (Typer → Toolable)**

Run:
```bash
# Find all imports of typer
grep -r "from typer import" tests/typer_tests/ | wc -l
grep -r "import typer" tests/typer_tests/ | wc -l
```

Expected: Count of imports to update

**Step 3: Replace imports using sed**

Run:
```bash
# Replace 'from typer import' with 'from toolable import'
find tests/typer_tests/ -name "*.py" -exec sed -i '' 's/from typer import/from toolable import/g' {} +

# Replace 'import typer' with 'import toolable as typer' (keeps test code working)
find tests/typer_tests/ -name "*.py" -exec sed -i '' 's/import typer$/import toolable as typer/g' {} +
```

Expected: Imports updated

**Step 4: Run Typer test suite**

Run:
```bash
pytest tests/typer_tests/ -v 2>&1 | tail -20
```

Expected: Most tests should pass (validates Typer functionality preserved)

**Step 5: Commit Typer tests**

Run:
```bash
git add tests/typer_tests/
git commit -m "test: add Typer test suite for baseline functionality

- Copy Typer's original test suite
- Update imports (typer → toolable)
- Validates that Typer functionality is preserved
- Baseline for ensuring no regressions"
```

Expected: Commit created

---

### Task 12: Test End-to-End with Real Example

**Files:**
- Create: `examples/git_tool.py`
- Test manually

**Step 1: Create realistic example**

Create `examples/git_tool.py`:

```python
#!/usr/bin/env python
"""Git operations tool for agents."""

import subprocess
from pathlib import Path

from toolable import Toolable
from toolable.errors import ErrorCode, ToolError

app = Toolable(name="git-tool", help="Git operations for AI agents")


@app.command()
def commit(
    message: str,
    files: list[str] = None,
    amend: bool = False,
):
    """Commit changes to git repository."""
    if not Path(".git").exists():
        raise ToolError(ErrorCode.PRECONDITION, "Not a git repository")

    cmd = ["git", "commit", "-m", message]
    if amend:
        cmd.append("--amend")
    if files:
        cmd.extend(files)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise ToolError(
            ErrorCode.INTERNAL,
            f"Git commit failed: {result.stderr}",
            recoverable=False
        )

    return {
        "committed": True,
        "message": message,
        "output": result.stdout,
    }


@app.command()
def status():
    """Get git status."""
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    return {
        "status": result.stdout,
        "clean": len(result.stdout.strip()) == 0,
    }


@app.resource(uri_pattern="/commits/{sha}", summary="Get commit details")
def get_commit(sha: str):
    """Fetch commit details by SHA."""
    result = subprocess.run(
        ["git", "show", sha, "--format=%H%n%an%n%ae%n%s"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise ToolError(ErrorCode.NOT_FOUND, f"Commit {sha} not found")

    lines = result.stdout.split("\n")
    return {
        "sha": lines[0],
        "author_name": lines[1],
        "author_email": lines[2],
        "subject": lines[3],
    }


app.register_resource(get_commit)


if __name__ == "__main__":
    app()
```

**Step 2: Test human mode (Typer behavior)**

Run:
```bash
cd /Users/dblspeak/projects/toolable
python examples/git_tool.py --help
```

Expected: Shows Typer-style help with commands

**Step 3: Test agent discovery**

Run:
```bash
python examples/git_tool.py --discover
```

Expected: JSON with tools (commit, status) and resource (/commits/{sha})

**Step 4: Test command manifest**

Run:
```bash
python examples/git_tool.py commit --manifest
```

Expected: JSON schema for commit command with message, files, amend params

**Step 5: Test JSON execution**

Run:
```bash
python examples/git_tool.py '{"command": "status", "params": {}}'
```

Expected: JSON response with git status

**Step 6: Commit example**

Run:
```bash
git add examples/git_tool.py
git commit -m "example: add git-tool demonstrating Toolable features

- Real-world git operations tool
- Shows human CLI mode (unchanged Typer)
- Shows agent mode (--discover, --manifest, JSON)
- Demonstrates @resource decorator
- Uses ToolError for error handling"
```

Expected: Commit created

---

### Task 13: Update All Tests to Use Toolable API

**Files:**
- Modify: All `tests/test_*.py` files (except typer_tests)
- Remove: Tests that no longer apply to Typer-based architecture

**Step 1: Identify tests that need updating**

Run:
```bash
# Find tests importing old API
grep -l "from toolable import.*AgentCLI" tests/test_*.py
grep -l "AgentCLI" tests/test_*.py
```

Expected: List of test files using old API

**Step 2: Update test imports globally**

Run:
```bash
# Replace AgentCLI with Toolable
find tests/ -name "test_*.py" -not -path "tests/typer_tests/*" -exec sed -i '' 's/AgentCLI/Toolable/g' {} +

# Remove old decorator imports
# Will need manual cleanup for @toolable decorator (now @app.command)
```

**Step 3: Rewrite incompatible tests**

Files like `test_cli.py`, `test_decorators.py` may have tests for old AgentCLI that don't apply.

Options:
- Remove tests for old CLI framework
- Rewrite tests for Toolable/Typer API
- Keep agent feature tests in `test_agent_features.py`

**Step 4: Run full test suite**

Run:
```bash
pytest tests/ -v 2>&1 | tail -30
```

Expected: See which tests pass/fail, identify what needs fixing

**Step 5: Create migration guide for tests**

This step might spawn multiple subtasks as we discover what tests need updating.

**Step 6: Commit test updates**

Run:
```bash
git add tests/
git commit -m "test: update tests for Typer-based architecture

- Replace AgentCLI with Toolable in imports
- Remove tests for old CLI framework
- Keep agent feature tests
- Typer baseline tests in typer_tests/"
```

Expected: Commit created

---

### Task 14: Add Streaming and Session Support

**Files:**
- Modify: `src/toolable/main.py`
- Already have: `src/toolable/streaming.py`, `src/toolable/session.py`

**Step 1: Add streaming detection to decorators**

The challenge: Typer doesn't have a concept of "streaming" commands.

Solution: Use function return type hint.

Edit `src/toolable/main.py`, update `_agent_execute_json`:

```python
def _agent_execute_json(self, json_input: str) -> None:
    """Handle JSON input execution."""
    import json
    from typing import get_type_hints
    from toolable.response import Response
    from toolable.errors import ToolError
    from toolable.streaming import run_streaming_tool, stream
    from toolable.session import run_session_tool, session

    # ... existing JSON parsing ...

    # Check if command returns generator (streaming/session)
    type_hints = get_type_hints(command_info.callback)
    return_type = type_hints.get("return", None)

    # Execute command
    try:
        result = command_info.callback(**params)

        # Detect streaming
        if return_type == stream or hasattr(result, '__next__'):
            run_streaming_tool(result)
            return

        # Detect session
        if return_type == session:
            run_session_tool(result)
            return

        # Normal result
        if isinstance(result, dict) and "status" in result:
            print(json.dumps(result))
        else:
            print(json.dumps(Response.success(result if isinstance(result, dict) else {"result": result})))

    except ToolError as e:
        print(json.dumps(e.to_response()))
    except Exception as e:
        print(json.dumps(Response.error("INTERNAL", str(e), recoverable=False)))
```

**Step 2: Test streaming**

Add to `tests/test_agent_features.py`:

```python
def test_streaming_command(monkeypatch, capsys):
    """Test streaming command execution."""
    from toolable.streaming import stream, StreamEvent

    app = Toolable()

    @app.command()
    def process(items: list[str]) -> stream:
        """Process items with progress."""
        for i, item in enumerate(items):
            yield StreamEvent.progress(f"Processing {item}")
        yield StreamEvent.result({"status": "success", "result": {"processed": len(items)}})

    monkeypatch.setattr(sys, "argv", ["app.py", '{"command": "process", "params": {"items": ["a", "b"]}}'])
    app()

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().split("\n") if line]

    # Should have progress events + result
    assert len(lines) >= 3
```

**Step 3: Run test**

Run:
```bash
pytest tests/test_agent_features.py::test_streaming_command -v
```

Expected: PASS

**Step 4: Commit streaming support**

Run:
```bash
git add src/toolable/main.py tests/test_agent_features.py
git commit -m "feat: add streaming and session support to agent mode

- Detect generator return types (stream, session)
- Route to run_streaming_tool or run_session_tool
- Reuse streaming.py and session.py modules
- Test verifies streaming works in JSON execution"
```

Expected: Commit created

---

### Task 15: Clean Up and Final Testing

**Files:**
- Remove: Unused files from old implementation
- Update: All documentation

**Step 1: Remove old unused files**

Run:
```bash
# These were replaced by Typer
rm -f .backup/toolable-original/*
rmdir .backup/toolable-original .backup

# Check what's left
ls -la src/toolable/
```

Expected: Clean directory structure

**Step 2: Run full test suite**

Run:
```bash
pytest tests/ --cov=toolable --cov-report=term
```

Expected: Get coverage report, identify gaps

**Step 3: Update README with complete examples**

Ensure README has:
- Installation
- Basic Typer usage (unchanged)
- Agent discovery example
- Agent JSON execution example
- Resource example
- Error handling example

**Step 4: Run CI locally**

Run:
```bash
# Run what CI will run
ruff check src/ tests/
pytest tests/
```

Expected: All checks pass

**Step 5: Final commit**

Run:
```bash
git add -A
git commit -m "refactor: complete Typer → Toolable transformation

Summary of changes:
- Forked Typer 0.15.1 as base
- Renamed Typer class → Toolable
- Added agent flag detection (--discover, --manifest, JSON)
- Integrated response/error envelopes
- Added @resource and @prompt decorators
- Preserved all Typer API and functionality
- Added comprehensive agent feature tests

Toolable now provides:
- Full Typer CLI framework
- Agent discovery and schema generation
- JSON input/output mode
- MCP-like features without server overhead

Migration from old toolable:
- AgentCLI → Toolable (better API)
- @toolable decorator → @app.command() (Typer standard)
- All response/error/streaming code preserved"
```

Expected: Commit created

**Step 6: Push to remote**

Run:
```bash
git push origin refactor/integrate-typer-fork
```

Expected: Branch pushed

---

## Phase 2: Testing and Refinement

### Task 16: Build 3-5 Real-World Tools

**Goal:** Validate the architecture with actual use cases

**Examples to build:**
1. **git-tool.py** (already have from Task 12)
2. **docker-tool.py** - Docker container operations
3. **file-tool.py** - File system operations
4. **api-tool.py** - HTTP API client wrapper
5. **db-tool.py** - Database query tool

Each should demonstrate:
- Multiple commands
- Type hints for automatic schemas
- Resource endpoints
- Error handling
- Both human and agent usage

**Step 1-5:** Build each tool as separate example file

**Step 6: Document lessons learned**

Create `docs/lessons-learned-typer-fork.md` with:
- What works well
- What's awkward
- API improvements needed
- Missing features

---

## Phase 3: Documentation and Polish

### Task 17: Complete Documentation

**Files:**
- Update: `README.md`
- Update: `CLAUDE.md`
- Update: `CONTRIBUTING.md`
- Create: `docs/migration-guide.md` (old toolable → new)
- Create: `docs/typer-comparison.md` (Toolable vs Typer)

**Step 1: Write migration guide**

Create `docs/migration-guide.md`:

```markdown
# Migration Guide: Old Toolable → Toolable 0.2.0

## What Changed

Toolable 0.2.0 is a complete rewrite based on Typer.

**Old (0.1.x):**
```python
from toolable import toolable, AgentCLI

@toolable(summary="Add")
def add(a: int, b: int):
    return {"sum": a + b}

AgentCLI(add).run()
```

**New (0.2.x):**
```python
from toolable import Toolable

app = Toolable()

@app.command()
def add(a: int, b: int):
    """Add two numbers."""
    return {"sum": a + b}

if __name__ == "__main__":
    app()
```

## Benefits

- Full Typer API available
- Better type hint support
- Rich output formatting
- Shell completion
- Better error messages
- Same agent features + better foundation
```

**Step 2: Write Typer comparison**

Create `docs/typer-comparison.md`:

```markdown
# Toolable vs Typer

## What Toolable Adds to Typer

| Feature | Typer | Toolable |
|---------|-------|----------|
| Type-hinted CLI | ✅ | ✅ |
| Rich output | ✅ | ✅ |
| Shell completion | ✅ | ✅ |
| `--discover` flag | ❌ | ✅ |
| `--manifest` flag | ❌ | ✅ |
| JSON input mode | ❌ | ✅ |
| Response envelopes | ❌ | ✅ |
| `@resource` decorator | ❌ | ✅ |
| `@prompt` decorator | ❌ | ✅ |
| Streaming support | ❌ | ✅ |
| Session support | ❌ | ✅ |

## Migration from Typer

```python
# Change this:
from typer import Typer

# To this:
from toolable import Toolable as Typer  # Alias for compatibility
```

Your existing code works unchanged!
```

**Step 3: Commit documentation**

Run:
```bash
git add docs/
git commit -m "docs: add migration guide and Typer comparison"
```

Expected: Commit created

---

## Success Criteria

- ✅ Typer functionality fully preserved
- ✅ Agent features working (--discover, --manifest, JSON)
- ✅ Response envelopes integrated
- ✅ @resource and @prompt decorators work
- ✅ Streaming/session support functional
- ✅ All tests passing
- ✅ Real-world examples demonstrate value
- ✅ Documentation complete

## Estimated Timeline

- **Phase 1 (Tasks 1-11):** 1 week - Fork, integrate, core agent features
- **Phase 2 (Task 12-16):** 3-5 days - Real-world validation
- **Phase 3 (Task 17):** 2-3 days - Documentation polish

**Total: 1.5-2 weeks** to production-ready Typer fork with agent features

## Key Risks

1. **Typer test suite compatibility** - Some tests may fail after rename, need debugging
2. **Type hint edge cases** - Complex types might not map to JSON schema cleanly
3. **API surface** - Need to ensure we're not breaking Typer's API contract

## Rollback Plan

If fork approach fails:
- Keep Typer fork in separate branch
- Fall back to AgentTyper wrapper (Option 1 from earlier analysis)
- Only ~1 week lost, lessons learned about Typer internals
