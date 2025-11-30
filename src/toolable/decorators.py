from collections.abc import Callable
from functools import wraps

from toolable.input import ToolInput

# Metadata storage
_TOOL_REGISTRY: dict[Callable, dict] = {}
_RESOURCE_REGISTRY: dict[Callable, dict] = {}
_PROMPT_REGISTRY: dict[Callable, dict] = {}


def toolable(
    summary: str,
    input_model: type[ToolInput] | None = None,
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
