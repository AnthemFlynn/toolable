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
from toolable.decorators import resource, prompt

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
]
