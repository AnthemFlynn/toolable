import json
import sys

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

    monkeypatch.setattr(
        sys, "argv", ["app.py", '{"command": "add", "params": {"a": 5, "b": 3}}']
    )
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
    from toolable.errors import ErrorCode, ToolError

    app = Toolable()

    @app.command()
    def divide(a: float, b: float):
        """Divide a by b."""
        if b == 0:
            raise ToolError(ErrorCode.INVALID_INPUT, "Cannot divide by zero")
        return {"result": a / b}

    monkeypatch.setattr(
        sys, "argv", ["app.py", '{"command": "divide", "params": {"a": 10, "b": 0}}']
    )
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"
    assert "divide by zero" in result["error"]["message"]


def test_streaming_command_execution(monkeypatch, capsys):
    """Test streaming command execution with JSON input."""
    from toolable.streaming import StreamEvent, stream

    app = Toolable()

    @app.command()
    def process_items(count: int) -> stream:
        """Process items with streaming progress."""
        for i in range(count):
            yield StreamEvent.progress(
                f"Processing item {i+1}/{count}", percent=int((i + 1) / count * 100)
            )
        yield StreamEvent.result({"status": "success", "result": {"processed": count}})

    monkeypatch.setattr(
        sys, "argv", ["app.py", '{"command": "process_items", "params": {"count": 3}}']
    )
    app()

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().split("\n") if line]

    # Should have progress events + result
    assert len(lines) == 4

    # Check first progress event
    event1 = json.loads(lines[0])
    assert event1["type"] == "progress"
    assert "Processing item 1/3" in event1["message"]

    # Check final result
    final = json.loads(lines[-1])
    assert final["type"] == "result"
    assert final["result"]["processed"] == 3


def test_discover_detects_streaming_mode(monkeypatch, capsys):
    """Test discovery correctly identifies streaming commands."""
    from toolable.streaming import StreamEvent, stream

    app = Toolable()

    @app.command()
    def normal_command():
        """Normal command."""
        return {"result": "ok"}

    @app.command()
    def streaming_command() -> stream:
        """Streaming command."""
        yield StreamEvent.result({"done": True})

    monkeypatch.setattr(sys, "argv", ["app.py", "--discover"])
    app()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    normal_tool = next(t for t in result["tools"] if t["name"] == "normal_command")
    streaming_tool = next(
        t for t in result["tools"] if t["name"] == "streaming_command"
    )

    assert normal_tool["streaming"] is False
    assert streaming_tool["streaming"] is True
