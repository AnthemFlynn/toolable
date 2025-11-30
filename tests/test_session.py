import pytest
from toolable.session import SessionEvent


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
