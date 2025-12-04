import json
import sys
from io import StringIO

from toolable import Toolable


def test_discover_lists_commands(monkeypatch, capsys):
    """Test --discover flag lists all registered commands."""
    app = Toolable()

    @app.command()
    def hello(name: str):
        """Say hello."""
        print(f"Hello {name}")

    @app.command()
    def goodbye(name: str):
        """Say goodbye."""
        print(f"Goodbye {name}")

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert "tools" in result
    assert len(result["tools"]) == 2
    assert any(t["name"] == "hello" for t in result["tools"])
    assert any(t["name"] == "goodbye" for t in result["tools"])


def test_discover_includes_command_summaries(monkeypatch, capsys):
    """Test discovery includes command summaries."""
    app = Toolable()

    @app.command()
    def hello(name: str):
        """Say hello to someone."""
        print(f"Hello {name}")

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    hello_tool = next(t for t in result["tools"] if t["name"] == "hello")
    assert "Say hello" in hello_tool["summary"]


def test_manifest_returns_command_schema(monkeypatch, capsys):
    """Test --manifest flag returns command schema."""
    app = Toolable()

    @app.command()
    def commit(
        message: str,
        files: list[str] = None,
        amend: bool = False,
    ):
        """Commit changes to git."""
        pass

    monkeypatch.setattr(sys, "argv", ["app.py", "commit", "--manifest"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["name"] == "commit"
    assert "schema" in result
    assert "properties" in result["schema"]
    assert "message" in result["schema"]["properties"]
    assert "files" in result["schema"]["properties"]
    assert "amend" in result["schema"]["properties"]
    assert result["schema"]["properties"]["message"]["type"] == "string"
