import json
import sys
from collections.abc import Generator
from typing import Any

# Type alias for session tools
session = Generator[dict[str, Any], dict[str, Any], None]


def emit_session(data: dict) -> None:
    """Emit session event to stdout."""
    print(json.dumps(data), flush=True)


def receive_session_input() -> dict:
    """Read session input from stdin."""
    line = sys.stdin.readline()
    if not line:
        return {"action": "quit"}
    return json.loads(line.strip())


def run_session_tool(gen: session) -> dict:
    """Execute a session tool with bidirectional communication."""
    try:
        # Get first yield (session_start)
        event = next(gen)
        emit_session(event)

        # Loop: receive input, send to generator, emit response
        while True:
            input_data = receive_session_input()
            try:
                event = gen.send(input_data)
                emit_session(event)

                if event.get("type") == "session_end":
                    break
            except StopIteration:
                break

        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "error": {"code": "INTERNAL", "message": str(e), "recoverable": False}}


class SessionEvent:
    """Helpers for creating session events."""

    @staticmethod
    def start(message: str, prompt: str = "> ") -> dict:
        return {"type": "session_start", "message": message, "prompt": prompt}

    @staticmethod
    def end(status: str = "success") -> dict:
        return {"type": "session_end", "status": status}

    @staticmethod
    def awaiting(prompt: str = "> ") -> dict:
        return {"type": "awaiting_input", "prompt": prompt}
