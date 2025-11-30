import pytest
import json
import sys
from io import StringIO
from toolable.notifications import notify


def test_notify_progress(capsys):
    """Test notify.progress()."""
    notify.progress("Processing...", percent=50)
    captured = capsys.readouterr()
    data = json.loads(captured.err.strip())

    assert data["type"] == "notification"
    assert data["kind"] == "progress"
    assert data["message"] == "Processing..."
    assert data["percent"] == 50


def test_notify_progress_without_percent(capsys):
    """Test notify.progress() without percent."""
    notify.progress("Starting...")
    captured = capsys.readouterr()
    data = json.loads(captured.err.strip())

    assert data["type"] == "notification"
    assert data["kind"] == "progress"
    assert data["message"] == "Starting..."
    assert "percent" not in data


def test_notify_log(capsys):
    """Test notify.log()."""
    notify.log("Something happened", level="info")
    captured = capsys.readouterr()
    data = json.loads(captured.err.strip())

    assert data["type"] == "notification"
    assert data["kind"] == "log"
    assert data["level"] == "info"
    assert data["message"] == "Something happened"


def test_notify_log_default_level(capsys):
    """Test notify.log() with default level."""
    notify.log("Info message")
    captured = capsys.readouterr()
    data = json.loads(captured.err.strip())

    assert data["level"] == "info"


def test_notify_artifact(capsys):
    """Test notify.artifact()."""
    notify.artifact("report.pdf", "file:///tmp/report.pdf")
    captured = capsys.readouterr()
    data = json.loads(captured.err.strip())

    assert data["type"] == "notification"
    assert data["kind"] == "artifact"
    assert data["name"] == "report.pdf"
    assert data["uri"] == "file:///tmp/report.pdf"
