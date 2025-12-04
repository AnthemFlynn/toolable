"""Decorators for resources, prompts, and backwards compatibility shims."""

import warnings
from collections.abc import Callable
from functools import wraps

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


def get_tool_meta(fn: Callable) -> dict | None:
    """Get @toolable decorator metadata (backwards compat)."""
    return getattr(fn, "_toolable_meta", None)


# Backwards compatibility: @toolable decorator (v0.1.x API)
def toolable(summary: str, **kwargs):
    """DEPRECATED: Use @app.command() instead.

    This decorator is provided for backwards compatibility with toolable 0.1.x.
    In 0.2.0, use Toolable's @app.command() decorator instead.

    Migration:
        Old: @toolable(summary="Do thing")
             def my_func(): ...
             AgentCLI(my_func).run()

        New: app = Toolable()
             @app.command()
             def my_func(): ...
             app()
    """
    warnings.warn(
        "@toolable decorator is deprecated. Use @app.command() instead. "
        "See migration guide for details.",
        DeprecationWarning,
        stacklevel=2
    )

    def decorator(fn: Callable) -> Callable:
        # Store metadata for backwards compat
        fn._toolable_meta = {"summary": summary, **kwargs}

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator
