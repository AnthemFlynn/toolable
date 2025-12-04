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
