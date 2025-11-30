import pytest
import json
import sys
from io import StringIO
from pydantic import Field
from toolable import (
    toolable,
    AgentCLI,
    ToolInput,
    Response,
    ToolError,
    ErrorCode,
)


def test_end_to_end_simple_tool(monkeypatch, capsys):
    """Test end-to-end execution of a simple tool."""
    @toolable(summary="Add two numbers")
    def add(a: int, b: int):
        """Add two numbers and return the sum."""
        return {"sum": a + b}

    cli = AgentCLI(add)

    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["add", '{"a": 5, "b": 3}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["sum"] == 8


def test_end_to_end_with_input_model(monkeypatch, capsys):
    """Test end-to-end with ToolInput model."""
    class AddInput(ToolInput):
        a: int = Field(description="First number")
        b: int = Field(description="Second number")

    @toolable(summary="Add numbers", input_model=AddInput)
    def add(input: AddInput):
        return {"sum": input.a + input.b}

    cli = AgentCLI(add)
    monkeypatch.setattr(sys, "argv", ["add", '{"a": 10, "b": 20}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["sum"] == 30


def test_end_to_end_validation_error(monkeypatch, capsys):
    """Test end-to-end with validation error."""
    class MyInput(ToolInput):
        name: str
        age: int

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        return {"message": f"{input.name} is {input.age}"}

    cli = AgentCLI(my_tool)
    monkeypatch.setattr(sys, "argv", ["my_tool", '{"name": "Alice"}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"


def test_end_to_end_tool_error(monkeypatch, capsys):
    """Test end-to-end with ToolError."""
    @toolable(summary="Divide")
    def divide(a: int, b: int):
        if b == 0:
            raise ToolError(
                ErrorCode.INVALID_INPUT,
                "Cannot divide by zero",
                suggestion="Use a non-zero divisor"
            )
        return {"result": a / b}

    cli = AgentCLI(divide)
    monkeypatch.setattr(sys, "argv", ["divide", '{"a": 10, "b": 0}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert response["error"]["message"] == "Cannot divide by zero"
    assert response["error"]["suggestion"] == "Use a non-zero divisor"


def test_end_to_end_discover(monkeypatch, capsys):
    """Test --discover flag."""
    @toolable(summary="Tool 1")
    def tool1():
        return {}

    @toolable(summary="Tool 2")
    def tool2():
        return {}

    cli = AgentCLI("mycli", tools=[tool1, tool2], version="1.0.0")
    monkeypatch.setattr(sys, "argv", ["mycli", "--discover"])
    cli.run()

    captured = capsys.readouterr()
    manifest = json.loads(captured.out)

    assert manifest["name"] == "mycli"
    assert manifest["version"] == "1.0.0"
    assert len(manifest["tools"]) == 2


def test_end_to_end_manifest(monkeypatch, capsys):
    """Test --manifest flag."""
    class MyInput(ToolInput):
        name: str = Field(description="User name")

    @toolable(summary="Greet user", input_model=MyInput)
    def greet(input: MyInput):
        """Greet a user by name."""
        return {"message": f"Hello {input.name}"}

    cli = AgentCLI(greet)
    monkeypatch.setattr(sys, "argv", ["greet", "--manifest"])
    cli.run()

    captured = capsys.readouterr()
    manifest = json.loads(captured.out)

    assert manifest["name"] == "greet"
    assert manifest["summary"] == "Greet user"
    assert manifest["description"] == "Greet a user by name."
    assert "schema" in manifest


def test_end_to_end_cli_flags(monkeypatch, capsys):
    """Test execution with CLI flags."""
    @toolable(summary="Echo")
    def echo(message: str, count: int = 1):
        return {"echoes": [message] * count}

    cli = AgentCLI(echo)
    monkeypatch.setattr(sys, "argv", ["echo", "--message", "hello", "--count", "3"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["echoes"] == ["hello", "hello", "hello"]


def test_end_to_end_dry_run(monkeypatch, capsys):
    """Test dry_run reserved field."""
    class MyInput(ToolInput):
        name: str
        dry_run: bool = False

    @toolable(summary="Create user", input_model=MyInput)
    def create_user(input: MyInput):
        return {"created": input.name}

    cli = AgentCLI(create_user)
    monkeypatch.setattr(sys, "argv", ["create_user", '{"name": "Alice", "dry_run": true}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["dry_run"] is True
    assert "would_execute" in response["result"]


def test_timeout_fires_on_unix(monkeypatch, capsys):
    """Test that timeout actually fires on Unix systems."""
    import time
    import platform

    # Skip on Windows
    if platform.system() == 'Windows':
        pytest.skip("Unix-only test")

    class TimeoutInput(ToolInput):
        timeout: int = 1

    @toolable(summary="Slow tool", input_model=TimeoutInput)
    def slow_tool(input: TimeoutInput):
        time.sleep(2)  # Sleep longer than timeout
        return {"result": "should not reach"}

    cli = AgentCLI(slow_tool)
    monkeypatch.setattr(sys, "argv", ["slow_tool", '{"timeout": 1}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "TIMEOUT"
