# Copied from pydantic 1.9.2 (the latest version to support python 3.6.)
# https://github.com/pydantic/pydantic/blob/v1.9.2/pydantic/typing.py
# Reduced drastically to only include Typer-specific 3.8+ functionality
# mypy: ignore-errors

import sys
import types
from collections.abc import Callable
from typing import (
    Annotated,
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


def is_union(tp: type[Any] | None) -> bool:
    return tp is Union or tp is types.UnionType  # noqa: E721


__all__ = (
    "NoneType",
    "is_none_type",
    "is_callable_type",
    "is_literal_type",
    "all_literal_values",
    "is_union",
    "Annotated",
    "Literal",
    "get_args",
    "get_origin",
    "get_type_hints",
)


NoneType = None.__class__


NONE_TYPES: tuple[Any, Any, Any] = (None, NoneType, Literal[None])


if sys.version_info[:2] == (3, 8):
    # We can use the fast implementation for 3.8 but there is a very weird bug
    # where it can fail for `Literal[None]`.
    # We just need to redefine a useless `Literal[None]` inside the function body to fix this

    def is_none_type(type_: Any) -> bool:
        Literal[None]  # fix edge case
        return any(type_ is none_type for none_type in NONE_TYPES)

else:

    def is_none_type(type_: Any) -> bool:
        return any(type_ is none_type for none_type in NONE_TYPES)


def is_callable_type(type_: type[Any]) -> bool:
    return type_ is Callable or get_origin(type_) is Callable


def is_literal_type(type_: type[Any]) -> bool:
    import typing_extensions

    return get_origin(type_) in (Literal, typing_extensions.Literal)


def literal_values(type_: type[Any]) -> tuple[Any, ...]:
    return get_args(type_)


def all_literal_values(type_: type[Any]) -> tuple[Any, ...]:
    """
    This method is used to retrieve all Literal values as
    Literal can be used recursively (see https://www.python.org/dev/peps/pep-0586)
    e.g. `Literal[Literal[Literal[1, 2, 3], "foo"], 5, None]`
    """
    if not is_literal_type(type_):
        return (type_,)

    values = literal_values(type_)
    return tuple(x for value in values for x in all_literal_values(value))
