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


def test_json_input_executes_command(monkeypatch, capsys):
    """Test JSON input executes command."""
    app = Toolable()

    @app.command()
    def add(a: int, b: int):
        """Add two numbers."""
        result = a + b
        # Return dict for agent mode
        return {"sum": result}

    monkeypatch.setattr(sys, "argv", ["app.py", '{"command": "add", "params": {"a": 5, "b": 3}}'])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["status"] == "success"
    assert result["result"]["sum"] == 8


def test_discover_includes_resources(monkeypatch, capsys):
    """Test discovery includes resources."""
    app = Toolable()

    @app.resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id, "content": "..."}

    app.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert len(result["resources"]) == 1
    assert result["resources"][0]["uri_pattern"] == "/files/{id}"


def test_json_execution_handles_tool_error(monkeypatch, capsys):
    """Test JSON execution properly handles ToolError."""
    from toolable.errors import ToolError, ErrorCode

    app = Toolable()

    @app.command()
    def divide(a: float, b: float):
        """Divide a by b."""
        if b == 0:
            raise ToolError(ErrorCode.INVALID_INPUT, "Cannot divide by zero")
        return {"result": a / b}

    monkeypatch.setattr(sys, "argv", ["app.py", '{"command": "divide", "params": {"a": 10, "b": 0}}'])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
    assert "divide by zero" in result["error"]["message"]
