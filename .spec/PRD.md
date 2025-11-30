# Task: Implement the Toolable Library

## Overview

Build `toolable`, a Python library that makes any CLI executable a full-featured agent tool without requiring a server. The library provides decorators, base classes, and a CLI runner that handles discovery, validation, execution, streaming, sessions, and LLM sampling callbacks.

## Installation Target

```bash
pip install toolable
```

## Core Design Principles

1. **Convention over configuration** — sensible defaults, explicit overrides
2. **Pydantic-native** — leverage Field() for schema generation
3. **Dual-mode** — works for humans (--help, --flags) and agents (--manifest, JSON)
4. **Stateless library, stateful tools** — library doesn't manage state, tools can
5. **Progressive disclosure** — discovery → schema → execution

## File Structure

```
toolable/
├── __init__.py          # Public API exports
├── decorators.py        # @toolable, @resource, @prompt
├── cli.py               # AgentCLI, flag routing
├── input.py             # ToolInput base class
├── response.py          # Response envelope helpers
├── errors.py            # ToolError, error codes
├── streaming.py         # stream type, jsonlines handling
├── session.py           # session type, bidirectional protocol
├── notifications.py     # notify module
├── sampling.py          # sample() function, callback handling
├── discovery.py         # Manifest/schema generation
├── registry.py          # ToolRegistry for external loading
├── py.typed             # PEP 561 marker
└── _version.py          # Version string

tests/
├── __init__.py
├── test_decorators.py
├── test_cli.py
├── test_input.py
├── test_response.py
├── test_errors.py
├── test_streaming.py
├── test_session.py
├── test_notifications.py
├── test_sampling.py
├── test_discovery.py
├── test_registry.py
└── test_integration.py

pyproject.toml
README.md
```

## Dependencies

```toml
[project]
dependencies = [
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff",
    "mypy",
]
```

---

## Implementation Specifications

### 1. `__init__.py` — Public API

```python
from toolable.decorators import toolable, resource, prompt
from toolable.cli import AgentCLI
from toolable.input import ToolInput
from toolable.response import Response
from toolable.errors import ToolError, ErrorCode
from toolable.streaming import stream
from toolable.session import session
from toolable.notifications import notify
from toolable.sampling import sample
from toolable.registry import ToolRegistry

__all__ = [
    "toolable",
    "resource", 
    "prompt",
    "AgentCLI",
    "ToolInput",
    "Response",
    "ToolError",
    "ErrorCode",
    "stream",
    "session",
    "notify",
    "sample",
    "ToolRegistry",
]

__version__ = "0.1.0"
```

---

### 2. `errors.py` — Error Handling

```python
from enum import Enum
from typing import Any

class ErrorCode(str, Enum):
    # Recoverable
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_PARAM = "MISSING_PARAM"
    INVALID_PATH = "INVALID_PATH"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    PRECONDITION = "PRECONDITION"
    
    # Not recoverable
    TIMEOUT = "TIMEOUT"
    PERMISSION = "PERMISSION"
    INTERNAL = "INTERNAL"
    DEPENDENCY = "DEPENDENCY"
    
    @property
    def recoverable(self) -> bool:
        return self in {
            ErrorCode.INVALID_INPUT,
            ErrorCode.MISSING_PARAM,
            ErrorCode.INVALID_PATH,
            ErrorCode.NOT_FOUND,
            ErrorCode.CONFLICT,
            ErrorCode.PRECONDITION,
        }

class ToolError(Exception):
    def __init__(
        self,
        code: str | ErrorCode,
        message: str,
        recoverable: bool | None = None,
        suggestion: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.code = ErrorCode(code) if isinstance(code, str) else code
        self.message = message
        self.recoverable = recoverable if recoverable is not None else self.code.recoverable
        self.suggestion = suggestion
        self.context = context
        super().__init__(message)
    
    def to_response(self) -> dict:
        """Convert to response envelope."""
        from toolable.response import Response
        return Response.error(
            code=self.code.value,
            message=self.message,
            recoverable=self.recoverable,
            suggestion=self.suggestion,
            context=self.context,
        )
```

---

### 3. `response.py` — Response Envelope

```python
from typing import Any

class Response:
    @staticmethod
    def success(result: dict[str, Any]) -> dict:
        return {"status": "success", "result": result}
    
    @staticmethod
    def error(
        code: str,
        message: str,
        recoverable: bool = False,
        suggestion: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict:
        error_obj = {
            "code": code,
            "message": message,
            "recoverable": recoverable,
        }
        if suggestion:
            error_obj["suggestion"] = suggestion
        if context:
            error_obj["context"] = context
        
        return {"status": "error", "error": error_obj}
    
    @staticmethod
    def partial(
        result: dict[str, Any],
        errors: list[dict],
        result_key: str | None = None,
    ) -> dict:
        # Auto-detect result key if not specified
        succeeded_count = 0
        if result_key:
            succeeded_count = len(result.get(result_key, []))
        else:
            for v in result.values():
                if isinstance(v, list):
                    succeeded_count = len(v)
                    break
        
        failed_count = len(errors)
        recoverable_count = sum(1 for e in errors if e.get("recoverable", False))
        
        # Determine status
        if failed_count == 0:
            status = "success"
        elif succeeded_count == 0:
            status = "error"
        else:
            status = "partial"
        
        response = {
            "status": status,
            "result": result,
            "summary": {
                "total": succeeded_count + failed_count,
                "succeeded": succeeded_count,
                "failed": failed_count,
                "recoverable_failures": recoverable_count,
            },
        }
        
        if errors:
            response["errors"] = errors
        
        return response
```

---

### 4. `input.py` — ToolInput Base Class

```python
from pydantic import BaseModel, ConfigDict
from typing import Any

class ToolInput(BaseModel):
    """Base class for toolable inputs."""
    
    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
    )
    
    # Reserved field names (subclasses define to activate):
    # working_dir: str   → chdir before execution
    # timeout: int       → kill after N seconds  
    # dry_run: bool      → validate only
    # verbose: bool      → extra detail in response
    
    def context(self) -> dict[str, Any]:
        """Override to inject runtime context."""
        return {}
    
    def pre_validate(self) -> None:
        """Override for validation requiring I/O.
        
        Called after Pydantic validation, before execution.
        Raise ToolError for recoverable input problems.
        """
        pass
    
    def to_log_safe(self) -> dict[str, Any]:
        """Override to redact sensitive fields for logging."""
        return self.model_dump()
```

---

### 5. `decorators.py` — @toolable, @resource, @prompt

```python
from functools import wraps
from typing import Any, Callable, Type
from toolable.input import ToolInput

# Metadata storage
_TOOL_REGISTRY: dict[Callable, dict] = {}
_RESOURCE_REGISTRY: dict[Callable, dict] = {}
_PROMPT_REGISTRY: dict[Callable, dict] = {}

def toolable(
    summary: str,
    input_model: Type[ToolInput] | None = None,
    examples: list[dict] | None = None,
    tags: list[str] | None = None,
    streaming: bool = False,
    session_mode: bool = False,
):
    """Decorator to mark a function as an agent-callable tool."""
    def decorator(fn: Callable) -> Callable:
        _TOOL_REGISTRY[fn] = {
            "summary": summary,
            "input_model": input_model,
            "examples": examples or [],
            "tags": tags or [],
            "streaming": streaming,
            "session_mode": session_mode,
            "fn": fn,
        }
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        # Attach metadata to wrapper
        wrapper._toolable_meta = _TOOL_REGISTRY[fn]
        return wrapper
    
    return decorator

def resource(
    uri_pattern: str,
    summary: str,
    mime_types: list[str] | None = None,
    tags: list[str] | None = None,
):
    """Decorator to mark a function as a resource provider."""
    def decorator(fn: Callable) -> Callable:
        _RESOURCE_REGISTRY[fn] = {
            "uri_pattern": uri_pattern,
            "summary": summary,
            "mime_types": mime_types or [],
            "tags": tags or [],
            "fn": fn,
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
    tags: list[str] | None = None,
):
    """Decorator to mark a function as a prompt template."""
    def decorator(fn: Callable) -> Callable:
        _PROMPT_REGISTRY[fn] = {
            "summary": summary,
            "arguments": arguments,
            "tags": tags or [],
            "fn": fn,
        }
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        wrapper._prompt_meta = _PROMPT_REGISTRY[fn]
        return wrapper
    
    return decorator

def get_tool_meta(fn: Callable) -> dict | None:
    return getattr(fn, "_toolable_meta", None)

def get_resource_meta(fn: Callable) -> dict | None:
    return getattr(fn, "_resource_meta", None)

def get_prompt_meta(fn: Callable) -> dict | None:
    return getattr(fn, "_prompt_meta", None)
```

---

### 6. `discovery.py` — Schema Generation

```python
import inspect
from typing import Any, Callable, get_type_hints
from pydantic import Field
from pydantic.fields import FieldInfo

def extract_schema_from_function(fn: Callable, input_model=None) -> dict:
    """Extract JSON schema from function signature or input model."""
    if input_model:
        return input_model.model_json_schema()
    
    hints = get_type_hints(fn)
    sig = inspect.signature(fn)
    
    properties = {}
    required = []
    
    for name, param in sig.parameters.items():
        if name in ("self", "cls", "input"):
            continue
        
        prop = {"type": _python_type_to_json(hints.get(name, str))}
        
        # Extract Field metadata if present
        if isinstance(param.default, FieldInfo):
            field: FieldInfo = param.default
            if field.description:
                prop["description"] = field.description
            if field.default is not None:
                prop["default"] = field.default
        elif param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(name)
        
        properties[name] = prop
    
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    
    return schema

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

def generate_tool_manifest(fn: Callable, meta: dict) -> dict:
    """Generate full manifest for a tool."""
    schema = extract_schema_from_function(fn, meta.get("input_model"))
    
    manifest = {
        "name": fn.__name__,
        "summary": meta["summary"],
        "description": inspect.getdoc(fn) or "",
        "streaming": meta.get("streaming", False),
        "session_mode": meta.get("session_mode", False),
        "schema": schema,
    }
    
    if meta.get("examples"):
        manifest["examples"] = meta["examples"]
    if meta.get("tags"):
        manifest["tags"] = meta["tags"]
    
    return manifest

def generate_resource_manifest(fn: Callable, meta: dict) -> dict:
    """Generate manifest for a resource."""
    return {
        "uri_pattern": meta["uri_pattern"],
        "summary": meta["summary"],
        "mime_types": meta.get("mime_types", []),
        "tags": meta.get("tags", []),
    }

def generate_prompt_manifest(fn: Callable, meta: dict) -> dict:
    """Generate manifest for a prompt."""
    return {
        "name": fn.__name__,
        "summary": meta["summary"],
        "arguments": meta["arguments"],
        "tags": meta.get("tags", []),
    }
```

---

### 7. `streaming.py` — Stream Support

```python
import sys
import json
from typing import Generator, Any

# Type alias for streaming tools
stream = Generator[dict[str, Any], None, None]

def emit_stream(data: dict) -> None:
    """Emit a single stream event as jsonline to stdout."""
    print(json.dumps(data), flush=True)

def run_streaming_tool(gen: stream) -> dict | None:
    """Execute a streaming tool, emitting events.
    
    Returns the final result if present.
    """
    final_result = None
    
    for event in gen:
        emit_stream(event)
        if event.get("type") == "result":
            final_result = event
    
    return final_result

class StreamEvent:
    """Helpers for creating stream events."""
    
    @staticmethod
    def progress(message: str, percent: int | None = None) -> dict:
        event = {"type": "progress", "message": message}
        if percent is not None:
            event["percent"] = percent
        return event
    
    @staticmethod
    def log(message: str, level: str = "info") -> dict:
        return {"type": "log", "level": level, "message": message}
    
    @staticmethod
    def artifact(name: str, uri: str) -> dict:
        return {"type": "artifact", "name": name, "uri": uri}
    
    @staticmethod
    def result(response: dict) -> dict:
        return {"type": "result", **response}
```

---

### 8. `session.py` — Bidirectional Sessions

```python
import sys
import json
from typing import Generator, Any

# Type alias for session tools
session = Generator[dict[str, Any], dict[str, Any], None]

def emit_session(data: dict) -> None:
    """Emit session event to stdout."""
    print(json.dumps(data), flush=True)

def receive_session_input() -> dict:
    """Read session input from stdin."""
    line = sys.stdin.readline()
    if not line:
        return {"action": "quit"}
    return json.loads(line.strip())

def run_session_tool(gen: session) -> dict:
    """Execute a session tool with bidirectional communication."""
    try:
        # Get first yield (session_start)
        event = next(gen)
        emit_session(event)
        
        # Loop: receive input, send to generator, emit response
        while True:
            input_data = receive_session_input()
            try:
                event = gen.send(input_data)
                emit_session(event)
                
                if event.get("type") == "session_end":
                    break
            except StopIteration:
                break
        
        return {"status": "success"}
    
    except Exception as e:
        return {"status": "error", "error": {"code": "INTERNAL", "message": str(e), "recoverable": False}}

class SessionEvent:
    """Helpers for creating session events."""
    
    @staticmethod
    def start(message: str, prompt: str = "> ") -> dict:
        return {"type": "session_start", "message": message, "prompt": prompt}
    
    @staticmethod
    def end(status: str = "success") -> dict:
        return {"type": "session_end", "status": status}
    
    @staticmethod
    def awaiting(prompt: str = "> ") -> dict:
        return {"type": "awaiting_input", "prompt": prompt}
```

---

### 9. `notifications.py` — Progress/Log to stderr

```python
import sys
import json

class _Notify:
    """Notification emitter (writes to stderr)."""
    
    def _emit(self, data: dict) -> None:
        print(json.dumps(data), file=sys.stderr, flush=True)
    
    def progress(self, message: str, percent: int | None = None) -> None:
        event = {
            "type": "notification",
            "kind": "progress",
            "message": message,
        }
        if percent is not None:
            event["percent"] = percent
        self._emit(event)
    
    def log(self, message: str, level: str = "info") -> None:
        self._emit({
            "type": "notification",
            "kind": "log",
            "level": level,
            "message": message,
        })
    
    def artifact(self, name: str, uri: str) -> None:
        self._emit({
            "type": "notification",
            "kind": "artifact",
            "name": name,
            "uri": uri,
        })

# Singleton instance
notify = _Notify()
```

---

### 10. `sampling.py` — LLM Callback

```python
import sys
import json
import uuid
import urllib.request
from typing import Any

# Global config for sample transport
_sample_config = {
    "via": "stdin",  # "stdin" or http URL
}

def configure_sampling(via: str) -> None:
    """Configure how sample() communicates with caller."""
    _sample_config["via"] = via

def sample(
    prompt: str,
    max_tokens: int = 1000,
    system: str | None = None,
    temperature: float | None = None,
    stop_sequences: list[str] | None = None,
) -> str:
    """Request LLM completion from caller. Blocks until response."""
    request_id = str(uuid.uuid4())[:8]
    
    request = {
        "type": "sample_request",
        "id": request_id,
        "prompt": prompt,
        "max_tokens": max_tokens,
    }
    if system:
        request["system"] = system
    if temperature is not None:
        request["temperature"] = temperature
    if stop_sequences:
        request["stop_sequences"] = stop_sequences
    
    via = _sample_config["via"]
    
    if via == "stdin":
        return _sample_via_stdin(request, request_id)
    elif via.startswith("http"):
        return _sample_via_http(request, via)
    else:
        raise ValueError(f"Unknown sample transport: {via}")

def _sample_via_stdin(request: dict, request_id: str) -> str:
    """Request sample via stdin/stdout protocol."""
    # Emit request
    print(json.dumps(request), flush=True)
    
    # Wait for response
    while True:
        line = sys.stdin.readline()
        if not line:
            raise RuntimeError("stdin closed while waiting for sample response")
        
        response = json.loads(line.strip())
        if response.get("type") == "sample_response" and response.get("id") == request_id:
            return response.get("content", "")

def _sample_via_http(request: dict, url: str) -> str:
    """Request sample via HTTP callback."""
    data = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    with urllib.request.urlopen(req) as resp:
        response = json.loads(resp.read().decode("utf-8"))
        return response.get("content", "")
```

---

### 11. `cli.py` — AgentCLI Runner

```python
import sys
import os
import json
import signal
import inspect
from typing import Callable, Any
from pydantic import ValidationError

from toolable.decorators import get_tool_meta, get_resource_meta, get_prompt_meta
from toolable.discovery import (
    generate_tool_manifest,
    generate_resource_manifest, 
    generate_prompt_manifest,
    extract_schema_from_function,
)
from toolable.response import Response
from toolable.errors import ToolError
from toolable.input import ToolInput
from toolable.streaming import run_streaming_tool
from toolable.session import run_session_tool
from toolable.sampling import configure_sampling

class AgentCLI:
    def __init__(
        self,
        name: str | Callable,
        tools: list[Callable] | None = None,
        version: str = "0.1.0",
    ):
        # Support single-tool shorthand: AgentCLI(my_func).run()
        if callable(name):
            fn = name
            self.name = fn.__name__
            self._tools = {fn.__name__: fn}
        else:
            self.name = name
            self._tools = {}
        
        self._resources = {}
        self._prompts = {}
        self.version = version
        
        # Register initial tools
        if tools:
            for tool in tools:
                self.register(tool)
    
    def register(self, fn: Callable, name: str | None = None) -> None:
        """Register a tool."""
        tool_name = name or fn.__name__
        self._tools[tool_name] = fn
    
    def register_resource(self, fn: Callable) -> None:
        """Register a resource."""
        meta = get_resource_meta(fn)
        if not meta:
            raise ValueError(f"{fn.__name__} is not decorated with @resource")
        self._resources[meta["uri_pattern"]] = fn
    
    def register_prompt(self, fn: Callable) -> None:
        """Register a prompt."""
        self._prompts[fn.__name__] = fn
    
    def run(self) -> None:
        """Execute CLI based on arguments."""
        args = sys.argv[1:]
        
        if not args or "--help" in args and len(args) == 1:
            self._print_help()
            return
        
        # Global flags
        if "--discover" in args:
            self._print_discover()
            return
        if "--tools" in args:
            self._print_tools()
            return
        if "--resources" in args:
            self._print_resources()
            return
        if "--prompts" in args:
            self._print_prompts()
            return
        
        # Resource fetch
        if "--resource" in args:
            idx = args.index("--resource")
            if idx + 1 < len(args):
                self._fetch_resource(args[idx + 1])
            return
        
        # Prompt render
        if "--prompt" in args:
            idx = args.index("--prompt")
            if idx + 2 < len(args):
                self._render_prompt(args[idx + 1], args[idx + 2])
            return
        
        # Tool execution
        cmd = args[0]
        if cmd not in self._tools:
            # Single tool mode
            if len(self._tools) == 1:
                cmd = list(self._tools.keys())[0]
                tool_args = args
            else:
                print(json.dumps(Response.error("NOT_FOUND", f"Unknown command: {cmd}", recoverable=True)))
                return
        else:
            tool_args = args[1:]
        
        self._run_tool(cmd, tool_args)
    
    def _run_tool(self, name: str, args: list[str]) -> None:
        """Execute a tool."""
        fn = self._tools[name]
        meta = get_tool_meta(fn) or {}
        
        # Handle tool-specific flags
        if "--manifest" in args:
            manifest = generate_tool_manifest(fn, meta)
            print(json.dumps(manifest, indent=2))
            return
        
        if "--help" in args:
            self._print_tool_help(fn, meta)
            return
        
        # Parse input
        streaming = "--stream" in args
        session_mode = "--session" in args
        
        # Configure sampling if specified
        if "--sample-via" in args:
            idx = args.index("--sample-via")
            if idx + 1 < len(args):
                configure_sampling(args[idx + 1])
        
        # Extract JSON input or parse flags
        json_input = None
        for arg in args:
            if arg.startswith("{"):
                json_input = arg
                break
        
        if "--validate" in args:
            idx = args.index("--validate")
            if idx + 1 < len(args):
                json_input = args[idx + 1]
            result = self._validate_input(fn, meta, json_input or "{}")
            print(json.dumps(result))
            return
        
        # Build params
        try:
            params = self._parse_input(fn, meta, args, json_input)
        except ValidationError as e:
            print(json.dumps(Response.error(
                "INVALID_INPUT",
                str(e),
                recoverable=True
            )))
            return
        except json.JSONDecodeError as e:
            print(json.dumps(Response.error(
                "INVALID_INPUT",
                f"Invalid JSON: {e}",
                recoverable=True
            )))
            return
        
        # Handle reserved fields
        input_obj = params if isinstance(params, ToolInput) else None
        
        if input_obj:
            # Run pre_validate hook
            try:
                input_obj.pre_validate()
            except ToolError as e:
                print(json.dumps(e.to_response()))
                return
            
            # Handle working_dir
            if hasattr(input_obj, "working_dir") and input_obj.working_dir:
                os.chdir(input_obj.working_dir)
            
            # Handle timeout
            if hasattr(input_obj, "timeout") and input_obj.timeout:
                signal.alarm(input_obj.timeout)
            
            # Handle dry_run
            if hasattr(input_obj, "dry_run") and input_obj.dry_run:
                print(json.dumps(Response.success({
                    "dry_run": True,
                    "would_execute": input_obj.to_log_safe()
                })))
                return
        
        # Execute tool
        try:
            if meta.get("input_model"):
                result = fn(params)
            else:
                if isinstance(params, dict):
                    result = fn(**params)
                else:
                    result = fn(params)
            
            # Handle different return types
            if meta.get("streaming") and streaming:
                run_streaming_tool(result)
            elif meta.get("session_mode") and session_mode:
                final = run_session_tool(result)
                print(json.dumps(final))
            elif isinstance(result, dict):
                # Check if already a response envelope
                if "status" in result:
                    print(json.dumps(result))
                else:
                    print(json.dumps(Response.success(result)))
            else:
                print(json.dumps(Response.success({"result": result})))
        
        except ToolError as e:
            print(json.dumps(e.to_response()))
        except Exception as e:
            print(json.dumps(Response.error(
                "INTERNAL",
                str(e),
                recoverable=False
            )))
    
    def _parse_input(self, fn: Callable, meta: dict, args: list[str], json_input: str | None) -> Any:
        """Parse input from JSON or CLI flags."""
        input_model = meta.get("input_model")
        
        if json_input:
            data = json.loads(json_input)
            if input_model:
                return input_model(**data)
            return data
        
        # Parse CLI flags into dict
        data = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--") and arg not in ("--stream", "--session", "--sample-via", "--manifest", "--help", "--validate"):
                key = arg[2:].replace("-", "_")
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    value = args[i + 1]
                    # Try to parse as JSON for complex types
                    try:
                        data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        data[key] = value
                    i += 2
                else:
                    data[key] = True
                    i += 1
            else:
                i += 1
        
        if input_model:
            return input_model(**data)
        return data
    
    def _validate_input(self, fn: Callable, meta: dict, json_input: str) -> dict:
        """Validate input without executing."""
        try:
            data = json.loads(json_input)
            input_model = meta.get("input_model")
            
            if input_model:
                obj = input_model(**data)
                obj.pre_validate()
            
            return {"valid": True}
        except ValidationError as e:
            return {"valid": False, "errors": e.errors()}
        except ToolError as e:
            return {"valid": False, "errors": [{"code": e.code.value, "message": e.message}]}
        except Exception as e:
            return {"valid": False, "errors": [{"message": str(e)}]}
    
    def _print_discover(self) -> None:
        """Print full discovery output."""
        output = {
            "name": self.name,
            "version": self.version,
            "tools": [],
            "resources": [],
            "prompts": [],
        }
        
        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {"summary": ""}
            output["tools"].append({
                "name": name,
                "summary": meta.get("summary", ""),
                "streaming": meta.get("streaming", False),
                "session_mode": meta.get("session_mode", False),
            })
        
        for pattern, fn in self._resources.items():
            meta = get_resource_meta(fn) or {}
            output["resources"].append(generate_resource_manifest(fn, meta))
        
        for name, fn in self._prompts.items():
            meta = get_prompt_meta(fn) or {}
            output["prompts"].append(generate_prompt_manifest(fn, meta))
        
        print(json.dumps(output, indent=2))
    
    def _print_tools(self) -> None:
        """Print tools only."""
        tools = []
        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {}
            tools.append({"name": name, "summary": meta.get("summary", "")})
        print(json.dumps({"tools": tools}, indent=2))
    
    def _print_resources(self) -> None:
        """Print resources only."""
        resources = []
        for fn in self._resources.values():
            meta = get_resource_meta(fn) or {}
            resources.append(generate_resource_manifest(fn, meta))
        print(json.dumps({"resources": resources}, indent=2))
    
    def _print_prompts(self) -> None:
        """Print prompts only."""
        prompts = []
        for fn in self._prompts.values():
            meta = get_prompt_meta(fn) or {}
            prompts.append(generate_prompt_manifest(fn, meta))
        print(json.dumps({"prompts": prompts}, indent=2))
    
    def _fetch_resource(self, uri: str) -> None:
        """Fetch a resource by URI."""
        import re
        
        for pattern, fn in self._resources.items():
            # Convert pattern to regex
            regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
            match = re.match(regex, uri)
            
            if match:
                params = match.groupdict()
                try:
                    result = fn(**params)
                    print(json.dumps(result))
                except Exception as e:
                    print(json.dumps(Response.error("INTERNAL", str(e))))
                return
        
        print(json.dumps(Response.error("NOT_FOUND", f"No resource matches URI: {uri}", recoverable=True)))
    
    def _render_prompt(self, name: str, json_args: str) -> None:
        """Render a prompt."""
        if name not in self._prompts:
            print(json.dumps(Response.error("NOT_FOUND", f"Unknown prompt: {name}", recoverable=True)))
            return
        
        try:
            args = json.loads(json_args)
            fn = self._prompts[name]
            result = fn(**args)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps(Response.error("INTERNAL", str(e))))
    
    def _print_help(self) -> None:
        """Print human-readable help."""
        print(f"{self.name} v{self.version}")
        print()
        print("Usage:")
        print(f"  {self.name} --discover              Show all tools, resources, prompts")
        print(f"  {self.name} <command> --manifest    Show command schema")
        print(f"  {self.name} <command> '{{}}'          Execute with JSON input")
        print(f"  {self.name} <command> --flag value  Execute with CLI flags")
        print()
        print("Commands:")
        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {}
            print(f"  {name:20} {meta.get('summary', '')}")
    
    def _print_tool_help(self, fn: Callable, meta: dict) -> None:
        """Print help for a specific tool."""
        print(f"{fn.__name__} - {meta.get('summary', '')}")
        print()
        if fn.__doc__:
            print(fn.__doc__)
            print()
        
        schema = extract_schema_from_function(fn, meta.get("input_model"))
        props = schema.get("properties", {})
        required = schema.get("required", [])
        
        if props:
            print("Parameters:")
            for name, prop in props.items():
                req = "*" if name in required else " "
                default = f" (default: {prop['default']})" if "default" in prop else ""
                desc = prop.get("description", "")
                print(f"  {req} --{name:15} {prop.get('type', 'string'):10} {desc}{default}")
```

---

### 12. `registry.py` — External Tool Loading

```python
import subprocess
import json
from pathlib import Path
from typing import Any

class ToolRegistry:
    """Registry for discovering and calling external toolable executables."""
    
    def __init__(self, tool_paths: list[Path | str]):
        self.tools: dict[str, dict] = {}
        self.resources: dict[str, dict] = {}
        self.prompts: dict[str, dict] = {}
        
        for path in tool_paths:
            self._load_tool(Path(path))
    
    def _load_tool(self, path: Path) -> None:
        """Load manifest from a toolable executable."""
        if not path.exists():
            return
        
        try:
            result = subprocess.run(
                [str(path), "--discover"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                manifest = json.loads(result.stdout)
                
                for tool in manifest.get("tools", []):
                    tool["_path"] = path
                    self.tools[tool["name"]] = tool
                
                for resource in manifest.get("resources", []):
                    resource["_path"] = path
                    self.resources[resource["uri_pattern"]] = resource
                
                for prompt in manifest.get("prompts", []):
                    prompt["_path"] = path
                    self.prompts[prompt["name"]] = prompt
        
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass
    
    def discover(self) -> dict[str, str]:
        """Return tool summaries for LLM context injection."""
        return {name: info["summary"] for name, info in self.tools.items()}
    
    def schema(self, name: str) -> dict:
        """Get full schema for a tool."""
        tool = self.tools.get(name)
        if not tool:
            raise KeyError(f"Unknown tool: {name}")
        
        path = tool["_path"]
        result = subprocess.run(
            [str(path), name, "--manifest"],
            capture_output=True,
            text=True,
        )
        
        return json.loads(result.stdout)
    
    def call(self, name: str, params: dict) -> dict:
        """Execute a tool and return response."""
        tool = self.tools.get(name)
        if not tool:
            return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"Unknown tool: {name}", "recoverable": True}}
        
        path = tool["_path"]
        result = subprocess.run(
            [str(path), name, json.dumps(params)],
            capture_output=True,
            text=True,
        )
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL",
                    "message": f"Invalid response: {result.stdout}",
                    "recoverable": False,
                }
            }
    
    def fetch_resource(self, uri: str) -> dict:
        """Fetch a resource by URI."""
        import re
        
        for pattern, info in self.resources.items():
            regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
            if re.match(regex, uri):
                path = info["_path"]
                result = subprocess.run(
                    [str(path), "--resource", uri],
                    capture_output=True,
                    text=True,
                )
                return json.loads(result.stdout)
        
        return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"No resource matches: {uri}", "recoverable": True}}
    
    def render_prompt(self, name: str, args: dict) -> dict:
        """Render a prompt."""
        prompt = self.prompts.get(name)
        if not prompt:
            return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"Unknown prompt: {name}", "recoverable": True}}
        
        path = prompt["_path"]
        result = subprocess.run(
            [str(path), "--prompt", name, json.dumps(args)],
            capture_output=True,
            text=True,
        )
        
        return json.loads(result.stdout)
```

---

## Testing Requirements

Write tests for each module covering:

1. **test_decorators.py** — decorator metadata attachment
2. **test_response.py** — all Response methods, edge cases
3. **test_errors.py** — ToolError creation, to_response()
4. **test_input.py** — ToolInput validation, reserved fields, hooks
5. **test_discovery.py** — schema extraction from functions and models
6. **test_cli.py** — flag parsing, routing, all execution paths
7. **test_streaming.py** — stream execution, event emission
8. **test_session.py** — bidirectional protocol
9. **test_notifications.py** — stderr output
10. **test_sampling.py** — stdin and HTTP modes
11. **test_registry.py** — external tool loading and calling
12. **test_integration.py** — end-to-end scenarios

---

## Implementation Order

1. `errors.py` — foundation
2. `response.py` — depends on nothing
3. `input.py` — depends on errors
4. `decorators.py` — depends on input
5. `discovery.py` — depends on decorators
6. `notifications.py` — standalone
7. `streaming.py` — standalone
8. `session.py` — standalone
9. `sampling.py` — standalone
10. `cli.py` — depends on everything
11. `registry.py` — depends on response
12. `__init__.py` — exports
13. Tests
14. `pyproject.toml`, `README.md`

---

## Deliverables

1. Complete implementation of all modules
2. Full test suite with >90% coverage
3. `pyproject.toml` with dependencies and metadata
4. `README.md` with usage examples
5. Type hints throughout (py.typed marker)

Begin by creating the file structure and implementing in the order specified.
```
