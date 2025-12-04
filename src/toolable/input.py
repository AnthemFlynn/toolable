"""Backwards compatibility: ToolInput from v0.1.x

In toolable 0.2.0, input validation is handled by Typer's type hints.
This module provides a compatibility shim for code using ToolInput.
"""

import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict


class ToolInput(BaseModel):
    """DEPRECATED: Toolable 0.2.0 uses function signatures for input validation.

    This class is provided for backwards compatibility with toolable 0.1.x.
    In 0.2.0, use type hints in your function signature instead.

    Migration:
        Old: class MyInput(ToolInput):
                 name: str
                 age: int

             @toolable(summary="...", input_model=MyInput)
             def my_func(input: MyInput): ...

        New: @app.command()
             def my_func(name: str, age: int): ...
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
    )

    def __init__(self, **data):
        warnings.warn(
            "ToolInput is deprecated. Use type hints in function signatures instead. "
            "See migration guide for details.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(**data)

    def context(self) -> dict[str, Any]:
        """Override to inject runtime context."""
        return {}

    def pre_validate(self) -> None:
        """Override for validation requiring I/O."""
        pass

    def to_log_safe(self) -> dict[str, Any]:
        """Override to redact sensitive fields for logging."""
        return self.model_dump()
