import pytest
import json
from io import StringIO
from toolable.streaming import emit_stream, run_streaming_tool, StreamEvent


def test_emit_stream(capsys):
    """Test emit_stream()."""
    emit_stream({"type": "progress", "message": "Working..."})
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())

    assert data["type"] == "progress"
    assert data["message"] == "Working..."


def test_stream_event_progress():
    """Test StreamEvent.progress()."""
    event = StreamEvent.progress("Loading...", percent=50)
    assert event == {"type": "progress", "message": "Loading...", "percent": 50}


def test_stream_event_progress_without_percent():
    """Test StreamEvent.progress() without percent."""
    event = StreamEvent.progress("Starting...")
    assert event == {"type": "progress", "message": "Starting..."}


def test_stream_event_log():
    """Test StreamEvent.log()."""
    event = StreamEvent.log("Debug message", level="debug")
    assert event == {"type": "log", "level": "debug", "message": "Debug message"}


def test_stream_event_artifact():
    """Test StreamEvent.artifact()."""
    event = StreamEvent.artifact("output.txt", "file:///tmp/output.txt")
    assert event == {"type": "artifact", "name": "output.txt", "uri": "file:///tmp/output.txt"}


def test_stream_event_result():
    """Test StreamEvent.result()."""
    response = {"status": "success", "result": {"value": 42}}
    event = StreamEvent.result(response)
    assert event["type"] == "result"
    assert event["status"] == "success"
    assert event["result"]["value"] == 42


def test_run_streaming_tool(capsys):
    """Test run_streaming_tool()."""
    def my_generator():
        yield StreamEvent.progress("Step 1")
        yield StreamEvent.progress("Step 2")
        yield StreamEvent.result({"status": "success", "result": {"done": True}})

    result = run_streaming_tool(my_generator())
    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().split("\n") if line]

    # Should emit 3 events
    assert len(lines) == 3

    # Check final result
    assert result["type"] == "result"
    assert result["status"] == "success"


def test_run_streaming_tool_no_result(capsys):
    """Test run_streaming_tool() with no result event."""
    def my_generator():
        yield StreamEvent.progress("Working...")
        yield StreamEvent.log("Done")

    result = run_streaming_tool(my_generator())
    assert result is None
