from typing import Any

from pydantic import BaseModel, ConfigDict


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
