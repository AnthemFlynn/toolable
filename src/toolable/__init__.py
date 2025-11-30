from toolable.cli import AgentCLI
from toolable.decorators import prompt, resource, toolable
from toolable.errors import ErrorCode, ToolError
from toolable.input import ToolInput
from toolable.notifications import notify
from toolable.registry import ToolRegistry
from toolable.response import Response
from toolable.sampling import sample
from toolable.session import session
from toolable.streaming import stream

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


def main() -> None:
    print("Hello from toolable!")
