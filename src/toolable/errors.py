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
        self.recoverable = (
            recoverable if recoverable is not None else self.code.recoverable
        )
        self.suggestion = suggestion
        self.context = context
        super().__init__(message)

    def to_response(self) -> dict:
        """Convert to response envelope.

        Note: Import is inside method to avoid circular dependency with response module.
        This is a common Python pattern for breaking import cycles.
        """
        from toolable.response import Response

        return Response.error(
            code=self.code.value,
            message=self.message,
            recoverable=self.recoverable,
            suggestion=self.suggestion,
            context=self.context,
        )
