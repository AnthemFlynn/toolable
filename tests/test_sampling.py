import json
import sys
from io import StringIO

import pytest

from toolable.sampling import _sample_config, configure_sampling, sample


def test_configure_sampling_stdin():
    """Test configure_sampling() with stdin."""
    configure_sampling("stdin")
    assert _sample_config["via"] == "stdin"


def test_configure_sampling_http():
    """Test configure_sampling() with HTTP URL."""
    configure_sampling("http://localhost:8000/sample")
    assert _sample_config["via"] == "http://localhost:8000/sample"


def test_sample_config_default():
    """Test default sample config."""
    # Reset to default
    configure_sampling("stdin")
    assert _sample_config["via"] == "stdin"


def test_sample_stdin_request_format(monkeypatch):
    """Test sample() emits correct request format via stdin."""
    configure_sampling("stdin")

    # Mock stdin with response - need to match the request ID
    fake_stdin = StringIO('{"type": "sample_response", "id": "test1234", "content": "AI response"}\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Mock uuid to get predictable request ID
    import uuid
    class MockUUID:
        def __str__(self):
            return "test12345678"
    monkeypatch.setattr(uuid, "uuid4", lambda: MockUUID())

    # Capture print calls to verify request format
    printed_requests = []
    def mock_print(*args, **kwargs):
        if args:
            printed_requests.append(args[0])

    monkeypatch.setattr("builtins.print", mock_print)

    # Call sample
    result = sample("Test prompt", max_tokens=100)

    # Parse the request that was emitted
    request_data = json.loads(printed_requests[0])

    # Verify request format
    assert request_data["type"] == "sample_request"
    assert request_data["id"] == "test1234"  # First 8 chars
    assert request_data["prompt"] == "Test prompt"
    assert request_data["max_tokens"] == 100

    # Verify response
    assert result == "AI response"


def test_sample_stdin_with_all_params(monkeypatch):
    """Test sample() with all optional parameters."""
    configure_sampling("stdin")

    # Mock stdin with response - match the 8-char ID
    fake_stdin = StringIO('{"type": "sample_response", "id": "abc12345", "content": "Full response"}\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Mock uuid
    import uuid
    class MockUUID:
        def __str__(self):
            return "abc123456789"
    monkeypatch.setattr(uuid, "uuid4", lambda: MockUUID())

    # Capture print calls
    printed_requests = []
    def mock_print(*args, **kwargs):
        if args:
            printed_requests.append(args[0])

    monkeypatch.setattr("builtins.print", mock_print)

    # Call sample with all params
    result = sample(
        prompt="Detailed prompt",
        max_tokens=500,
        system="You are helpful",
        temperature=0.7,
        stop_sequences=["STOP", "END"]
    )

    # Parse the request
    request_data = json.loads(printed_requests[0])

    # Verify all params are included
    assert request_data["type"] == "sample_request"
    assert request_data["prompt"] == "Detailed prompt"
    assert request_data["max_tokens"] == 500
    assert request_data["system"] == "You are helpful"
    assert request_data["temperature"] == 0.7
    assert request_data["stop_sequences"] == ["STOP", "END"]

    # Verify response
    assert result == "Full response"


def test_sample_stdin_waits_for_matching_id(monkeypatch):
    """Test sample() ignores responses with non-matching IDs."""
    configure_sampling("stdin")

    # Mock stdin with multiple responses, only last matches - ID is first 8 chars
    responses = [
        '{"type": "sample_response", "id": "wrong1", "content": "Wrong"}\n',
        '{"type": "other_message", "data": "ignore"}\n',
        '{"type": "sample_response", "id": "correct1", "content": "Correct response"}\n'
    ]
    fake_stdin = StringIO(''.join(responses))
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Mock uuid - first 8 chars will be "correct1"
    import uuid
    class MockUUID:
        def __str__(self):
            return "correct12345"
    monkeypatch.setattr(uuid, "uuid4", lambda: MockUUID())

    # Mock print to suppress output
    printed_requests = []
    def mock_print(*args, **kwargs):
        if args:
            printed_requests.append(args[0])

    monkeypatch.setattr("builtins.print", mock_print)

    # Call sample
    result = sample("Test", max_tokens=100)

    # Should return the response with matching ID
    assert result == "Correct response"


def test_sample_stdin_closed_error(monkeypatch):
    """Test sample() raises error when stdin closes."""
    configure_sampling("stdin")

    # Mock stdin that returns empty (closed)
    fake_stdin = StringIO('')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="stdin closed"):
        sample("Test prompt")


def test_sample_invalid_transport():
    """Test sample() with invalid transport raises error."""
    configure_sampling("unknown_transport")

    with pytest.raises(ValueError, match="Unknown sample transport"):
        sample("Test prompt")
