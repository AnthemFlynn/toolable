"""Toolable, build great CLIs with agent features. Based on Typer."""

__version__ = "0.2.0"

# Import main class (renamed from Typer)
from toolable.main import Toolable

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

# Re-export decorators
from toolable.decorators import resource, prompt, toolable

# Backwards compatibility imports (deprecated in 0.2.0)
from toolable.input import ToolInput
from toolable.cli import AgentCLI

__all__ = [
    # Main class
    "Toolable",
    # Utilities
    "Argument",
    "Option",
    "FileText",
    "FileTextWrite",
    "FileBinaryRead",
    "FileBinaryWrite",
    # Decorators
    "resource",
    "prompt",
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
    # Backwards compatibility (deprecated)
    "toolable",
    "ToolInput",
    "AgentCLI",
]
