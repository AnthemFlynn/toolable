import json
from collections.abc import Generator
from typing import Any

# Type alias for streaming tools
stream = Generator[dict[str, Any], None, None]


def emit_stream(data: dict) -> None:
    """Emit a single stream event as jsonline to stdout."""
    print(json.dumps(data), flush=True)


def run_streaming_tool(gen: stream) -> dict | None:
    """Execute a streaming tool, emitting events.

    Returns the final result if present.
    """
    final_result = None

    for event in gen:
        emit_stream(event)
        if event.get("type") == "result":
            final_result = event

    return final_result


class StreamEvent:
    """Helpers for creating stream events."""

    @staticmethod
    def progress(message: str, percent: int | None = None) -> dict:
        event = {"type": "progress", "message": message}
        if percent is not None:
            event["percent"] = percent
        return event

    @staticmethod
    def log(message: str, level: str = "info") -> dict:
        return {"type": "log", "level": level, "message": message}

    @staticmethod
    def artifact(name: str, uri: str) -> dict:
        return {"type": "artifact", "name": name, "uri": uri}

    @staticmethod
    def result(response: dict) -> dict:
        return {"type": "result", **response}
