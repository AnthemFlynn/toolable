import pytest
import sys
import json
from io import StringIO
from toolable.session import SessionEvent, run_session_tool


def test_session_event_start():
    """Test SessionEvent.start()."""
    event = SessionEvent.start("Welcome!", prompt=">> ")
    assert event == {
        "type": "session_start",
        "message": "Welcome!",
        "prompt": ">> "
    }


def test_session_event_start_default_prompt():
    """Test SessionEvent.start() with default prompt."""
    event = SessionEvent.start("Hello")
    assert event["prompt"] == "> "


def test_session_event_end():
    """Test SessionEvent.end()."""
    event = SessionEvent.end(status="success")
    assert event == {"type": "session_end", "status": "success"}


def test_session_event_end_default_status():
    """Test SessionEvent.end() with default status."""
    event = SessionEvent.end()
    assert event["status"] == "success"


def test_session_event_awaiting():
    """Test SessionEvent.awaiting()."""
    event = SessionEvent.awaiting(prompt="? ")
    assert event == {"type": "awaiting_input", "prompt": "? "}


def test_session_event_awaiting_default_prompt():
    """Test SessionEvent.awaiting() with default prompt."""
    event = SessionEvent.awaiting()
    assert event["prompt"] == "> "


def test_run_session_tool_full_flow(monkeypatch):
    """Test full session tool execution flow."""
    def my_session():
        yield SessionEvent.start("Started")
        user_input = yield SessionEvent.awaiting()
        yield {"type": "response", "data": user_input.get("value")}
        yield SessionEvent.end()

    # Mock stdin with user input
    fake_stdin = StringIO('{"value": "test"}\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(my_session())

    assert result["status"] == "success"
    assert len(outputs) >= 3  # At least start, awaiting, response, and end events

    # Verify start event was emitted
    start_event = json.loads(outputs[0])
    assert start_event["type"] == "session_start"
    assert start_event["message"] == "Started"


def test_session_tool_generator_error(monkeypatch):
    """Test session tool that raises exception."""
    def broken_session():
        yield SessionEvent.start("Start")
        raise ValueError("Broken!")

    # Mock stdin
    fake_stdin = StringIO()
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(broken_session())

    assert result["status"] == "error"
    assert result["error"]["code"] == "INTERNAL"
    assert "Broken!" in result["error"]["message"]


def test_session_tool_early_stop_iteration(monkeypatch):
    """Test session tool that stops iteration early."""
    def early_stop_session():
        yield SessionEvent.start("Start")
        # Generator ends without session_end event
        return

    # Mock stdin
    fake_stdin = StringIO()
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(early_stop_session())

    # Should still return success even if generator ends early
    assert result["status"] == "success"


def test_session_tool_quit_action(monkeypatch):
    """Test session tool with quit action from empty stdin."""
    def quit_session():
        yield SessionEvent.start("Start")
        user_input = yield SessionEvent.awaiting()
        # If user quits, we should handle it gracefully
        if user_input.get("action") == "quit":
            yield SessionEvent.end(status="cancelled")

    # Mock stdin with empty line (EOF)
    fake_stdin = StringIO('')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(quit_session())

    # Should complete successfully
    assert result["status"] == "success"


def test_session_tool_multiple_inputs(monkeypatch):
    """Test session tool with multiple user inputs.

    Note: Due to generator semantics, input sent at step N is assigned to yield from step N-1.
    So we use the pattern: yield awaiting -> value arrives on next send -> yield awaiting -> etc.
    """
    def multi_input_session():
        yield SessionEvent.start("Calculator")

        # Pattern: yield awaiting, then next send provides that input
        # But the input is assigned when we yield AGAIN
        input1 = yield SessionEvent.awaiting("Enter first number: ")
        input2 = yield SessionEvent.awaiting("Enter second number: ")

        first = input1.get("number", 0) if input1 else 0
        second = input2.get("number", 0) if input2 else 0

        # Result
        yield {"type": "result", "sum": first + second}
        yield SessionEvent.end()

    # Due to the generator send semantics, we need 3 inputs:
    # Input 0 (dummy): Sent with first awaiting, assigned on second awaiting -> input1
    # Input 1: Sent with second awaiting, assigned on result yield -> input2
    # Input 2: Sent to continue to end
    # So the SECOND input becomes input1, THIRD becomes input2
    fake_stdin = StringIO('{}\n{"number": 5}\n{"number": 10}\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(multi_input_session())

    assert result["status"] == "success"

    # Find result event
    result_event = None
    for output in outputs:
        event = json.loads(output)
        if event.get("type") == "result":
            result_event = event
            break

    assert result_event is not None
    assert result_event["sum"] == 15


def test_session_tool_error_during_send(monkeypatch):
    """Test session tool that raises error when receiving input."""
    def error_on_input_session():
        yield SessionEvent.start("Start")
        # Get input via yield awaiting pattern
        user_input = yield SessionEvent.awaiting()
        # Second yield to trigger another read and assignment of user_input
        yield {"type": "processing"}
        # Process the input and potentially error
        if user_input and user_input.get("trigger_error"):
            raise RuntimeError("Error processing input")
        yield SessionEvent.end()

    # Mock stdin with error-triggering input
    # Line 1: dummy input, read and sent with first awaiting yield
    # Line 2: the actual trigger input, assigned to user_input when we yield "processing"
    # Line 3: continue execution
    fake_stdin = StringIO('{}\n{"trigger_error": true}\n{}\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(error_on_input_session())

    # Error should be caught by outer try-except
    assert result["status"] == "error"
    assert result["error"]["code"] == "INTERNAL"
    assert "Error processing input" in result["error"]["message"]


def test_session_tool_handles_json_decode_error(monkeypatch):
    """Test session tool with invalid JSON input."""
    def json_session():
        yield SessionEvent.start("Start")
        yield SessionEvent.awaiting()
        user_input = yield
        yield {"type": "received", "data": user_input}
        yield SessionEvent.end()

    # Mock stdin with invalid JSON
    fake_stdin = StringIO('not valid json\n')
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    # Capture stdout
    outputs = []
    def capture_print(*args, **kwargs):
        if args:
            outputs.append(args[0])

    monkeypatch.setattr("builtins.print", capture_print)

    result = run_session_tool(json_session())

    # JSON decode error should be caught
    assert result["status"] == "error"
    assert result["error"]["code"] == "INTERNAL"
