import sys
import json
import uuid
import urllib.request
from typing import Any

# Global config for sample transport
_sample_config = {
    "via": "stdin",  # "stdin" or http URL
}


def configure_sampling(via: str) -> None:
    """Configure how sample() communicates with caller."""
    _sample_config["via"] = via


def sample(
    prompt: str,
    max_tokens: int = 1000,
    system: str | None = None,
    temperature: float | None = None,
    stop_sequences: list[str] | None = None,
) -> str:
    """Request LLM completion from caller. Blocks until response."""
    request_id = str(uuid.uuid4())[:8]

    request = {
        "type": "sample_request",
        "id": request_id,
        "prompt": prompt,
        "max_tokens": max_tokens,
    }
    if system:
        request["system"] = system
    if temperature is not None:
        request["temperature"] = temperature
    if stop_sequences:
        request["stop_sequences"] = stop_sequences

    via = _sample_config["via"]

    if via == "stdin":
        return _sample_via_stdin(request, request_id)
    elif via.startswith("http"):
        return _sample_via_http(request, via)
    else:
        raise ValueError(f"Unknown sample transport: {via}")


def _sample_via_stdin(request: dict, request_id: str) -> str:
    """Request sample via stdin/stdout protocol."""
    # Emit request
    print(json.dumps(request), flush=True)

    # Wait for response
    while True:
        line = sys.stdin.readline()
        if not line:
            raise RuntimeError("stdin closed while waiting for sample response")

        response = json.loads(line.strip())
        if response.get("type") == "sample_response" and response.get("id") == request_id:
            return response.get("content", "")


def _sample_via_http(request: dict, url: str) -> str:
    """Request sample via HTTP callback."""
    data = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        response = json.loads(resp.read().decode("utf-8"))
        return response.get("content", "")
