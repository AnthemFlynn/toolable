# Migration Guide: toolable 0.1.x → 0.2.0

## Overview

Toolable 0.2.0 is a complete architecture rewrite based on [Typer](https://github.com/fastapi/typer). The new version provides the same agent features with a better foundation and Typer's full API.

**TL;DR:** Change from custom framework to Typer + agent features built-in.

---

## Breaking Changes

### 1. Main Class: AgentCLI → Toolable

**Before (0.1.x):**
```python
from toolable import AgentCLI, toolable

@toolable(summary="Add numbers")
def add(a: int, b: int):
    return {"sum": a + b}

cli = AgentCLI(add)
cli.run()
```

**After (0.2.0):**
```python
from toolable import Toolable

app = Toolable()

@app.command()
def add(a: int, b: int):
    """Add numbers."""
    return {"sum": a + b}

if __name__ == "__main__":
    app()
```

### 2. Decorator: @toolable → @app.command()

The `@toolable` decorator is replaced by Typer's `@app.command()`:

**Before:**
```python
@toolable(summary="Do thing", tags=["example"])
def my_func():
    pass
```

**After:**
```python
@app.command()  # Summary comes from docstring
def my_func():
    """Do thing."""  # First line becomes summary
    pass
```

### 3. Input Models: ToolInput → Type Hints

**Before:**
```python
class MyInput(ToolInput):
    name: str = Field(description="User name")
    age: int = 18

@toolable(summary="Create user", input_model=MyInput)
def create_user(input: MyInput):
    return {"name": input.name}
```

**After:**
```python
from toolable.params import Option

@app.command()
def create_user(
    name: str = Option(..., help="User name"),
    age: int = 18
):
    """Create user."""
    return {"name": name}
```

---

## API Changes

### Commands

| 0.1.x | 0.2.0 |
|-------|-------|
| `@toolable(summary="...")` | `@app.command()` |
| `AgentCLI(func).run()` | `app = Toolable(); @app.command(); app()` |
| `input_model=MyInput` | Type hints in signature |
| `AgentCLI("name", tools=[...])` | `app.command()` for each function |

### Resources

| 0.1.x | 0.2.0 |
|-------|-------|
| `@resource(...); cli.register_resource(fn)` | `@app.resource(...); app.register_resource(fn)` |

**Same in both versions!** Resources work the same way.

### Responses

| 0.1.x | 0.2.0 |
|-------|-------|
| `Response.success(...)` | `Response.success(...)` ✅ Unchanged |
| `ToolError(ErrorCode.X, ...)` | `ToolError(ErrorCode.X, ...)` ✅ Unchanged |
| `StreamEvent.progress(...)` | `StreamEvent.progress(...)` ✅ Unchanged |

**All response/error handling unchanged!**

---

## What Stays the Same

✅ **Response envelopes** - `Response.success/error/partial`
✅ **Error codes** - `ErrorCode` enum
✅ **ToolError** - Exception class
✅ **Streaming** - `-> stream` and `StreamEvent`
✅ **Sessions** - `-> session` and `SessionEvent`
✅ **Notifications** - `notify.progress/log/artifact`
✅ **Sampling** - `sample()` function
✅ **Resources** - `@app.resource()` decorator
✅ **Prompts** - `@app.prompt_template()` decorator

---

## Agent Protocol Changes

### Discovery

**Before:**
```bash
python tool.py --discover
```

**After:**
```bash
python tool.py --discover  # Same!
```

✅ **No change** - discovery works the same.

### Manifest

**Before:**
```bash
python tool.py my_command --manifest
```

**After:**
```bash
python tool.py my_command --manifest  # Same!
```

✅ **No change** - manifest works the same.

### JSON Execution

**Before:**
```bash
python tool.py '{"a": 5, "b": 3}'  # Positional params
```

**After:**
```bash
python tool.py '{"command": "add", "params": {"a": 5, "b": 3}}'
```

⚠️ **Changed** - Must specify command name and params explicitly.

---

## Migration Steps

### Step 1: Update Imports

```python
# Change this:
from toolable import AgentCLI, toolable

# To this:
from toolable import Toolable
```

### Step 2: Create App Instance

```python
# Add this at module level:
app = Toolable()
```

### Step 3: Replace @toolable with @app.command()

```python
# Before:
@toolable(summary="Do thing")
def my_func():
    pass

# After:
@app.command()
def my_func():
    """Do thing."""  # Docstring becomes summary
    pass
```

### Step 4: Replace AgentCLI with app()

```python
# Before:
if __name__ == "__main__":
    AgentCLI(my_func).run()

# After:
if __name__ == "__main__":
    app()
```

### Step 5: Convert ToolInput to Type Hints

```python
# Before:
class MyInput(ToolInput):
    name: str
    count: int = 5

@toolable(summary="X", input_model=MyInput)
def func(input: MyInput):
    print(input.name)

# After:
@app.command()
def func(name: str, count: int = 5):
    """X"""
    print(name)
```

---

## Backwards Compatibility

Toolable 0.2.0 includes **deprecation shims** for smooth migration:

```python
# These still import (with warnings):
from toolable import toolable, ToolInput, AgentCLI

# But will emit DeprecationWarning guiding you to new API
```

**Recommendation:** Use warnings to find migration points, update gradually.

---

## Benefits of 0.2.0

### What You Get

✅ **Full Typer API** - All Typer features available
✅ **Better type hints** - Rich type system for schemas
✅ **Shell completion** - Bash/Zsh/Fish auto-complete
✅ **Rich output** - Beautiful terminal formatting
✅ **Better errors** - Typer's improved error messages
✅ **Proven foundation** - Built on 18K-star project
✅ **Same agent features** - Discovery, schemas, JSON, MCP-like

### What You Give Up

❌ **`input_model` parameter** - Use type hints instead
❌ **`AgentCLI` shortcuts** - More explicit app.command() style
❌ **Direct function wrapping** - Must use Typer app pattern

---

## Timeline

- **0.1.x maintenance:** Security fixes only
- **0.2.0:** Current development (Typer fork)
- **1.0.0:** Stable release after validation

---

## Getting Help

- See `examples/demo_tool.py` for working 0.2.0 code
- See `docs/feature-showcase.md` for all features
- Open an issue for migration questions
- Deprecation warnings include migration hints

---

## Credits

Toolable 0.2.0 is based on [Typer](https://github.com/fastapi/typer) by Sebastián Ramírez.
Agent features and MCP-like capabilities added by AnthemFlynn.
