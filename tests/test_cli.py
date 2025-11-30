import pytest
import json
import sys
from io import StringIO
from pydantic import Field
from toolable.cli import AgentCLI
from toolable.decorators import toolable, resource, prompt
from toolable.input import ToolInput


def test_agent_cli_single_tool_shorthand():
    """Test AgentCLI with single tool shorthand."""
    @toolable(summary="Test tool")
    def my_tool():
        return {"message": "hello"}

    cli = AgentCLI(my_tool)
    assert cli.name == "my_tool"
    assert "my_tool" in cli._tools


def test_agent_cli_register_tool():
    """Test registering tools."""
    @toolable(summary="Tool A")
    def tool_a():
        return "a"

    @toolable(summary="Tool B")
    def tool_b():
        return "b"

    cli = AgentCLI("mycli", tools=[tool_a, tool_b])
    assert "tool_a" in cli._tools
    assert "tool_b" in cli._tools


def test_agent_cli_register_resource():
    """Test registering resources."""
    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id}

    cli = AgentCLI("mycli")
    cli.register_resource(get_file)
    assert "/files/{id}" in cli._resources


def test_agent_cli_register_prompt():
    """Test registering prompts."""
    @prompt(summary="Greet", arguments={"name": "Name"})
    def greet(name: str):
        return f"Hello {name}"

    cli = AgentCLI("mycli")
    cli.register_prompt(greet)
    assert "greet" in cli._prompts


def test_parse_input_from_json():
    """Test _parse_input() with JSON."""
    @toolable(summary="Test")
    def my_tool(name: str, count: int):
        pass

    cli = AgentCLI("test")
    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    params = cli._parse_input(my_tool, meta or {}, [], '{"name": "test", "count": 5}')

    assert params == {"name": "test", "count": 5}


def test_parse_input_from_flags():
    """Test _parse_input() with CLI flags."""
    @toolable(summary="Test")
    def my_tool(name: str, count: int):
        pass

    cli = AgentCLI("test")
    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    args = ["--name", "test", "--count", "5"]
    params = cli._parse_input(my_tool, meta or {}, args, None)

    assert params == {"name": "test", "count": 5}


def test_parse_input_boolean_flag():
    """Test _parse_input() with boolean flags."""
    @toolable(summary="Test")
    def my_tool(verbose: bool):
        pass

    cli = AgentCLI("test")
    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    args = ["--verbose"]
    params = cli._parse_input(my_tool, meta or {}, args, None)

    assert params == {"verbose": True}


def test_validate_input_valid():
    """Test _validate_input() with valid input."""
    class MyInput(ToolInput):
        name: str

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        pass

    cli = AgentCLI("test")
    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    result = cli._validate_input(my_tool, meta, '{"name": "test"}')

    assert result["valid"] is True


def test_validate_input_invalid():
    """Test _validate_input() with invalid input."""
    class MyInput(ToolInput):
        name: str
        count: int

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        pass

    cli = AgentCLI("test")
    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    result = cli._validate_input(my_tool, meta, '{"name": "test"}')

    assert result["valid"] is False
    assert "errors" in result


def test_print_discover(capsys):
    """Test _print_discover()."""
    @toolable(summary="Test tool")
    def my_tool():
        pass

    cli = AgentCLI("mycli", tools=[my_tool])
    cli._print_discover()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["name"] == "mycli"
    assert data["version"] == "0.1.0"
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "my_tool"
    assert data["tools"][0]["summary"] == "Test tool"


def test_missing_resource_uri(monkeypatch, capsys):
    """Test --resource flag without URI argument."""
    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id}

    cli = AgentCLI("test")
    cli.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["test", "--resource"])
    cli.run()

    # Currently returns silently - should this be an error?
    # For now, just test current behavior
    captured = capsys.readouterr()
    # No output expected with current implementation
    assert captured.out == ""


def test_missing_prompt_arguments(monkeypatch, capsys):
    """Test --prompt flag without name or args."""
    @prompt(summary="Test", arguments={"name": "Name"})
    def my_prompt(name: str):
        return f"Hello {name}"

    cli = AgentCLI("test")
    cli.register_prompt(my_prompt)

    # Missing both name and args
    monkeypatch.setattr(sys, "argv", ["test", "--prompt"])
    cli.run()

    captured = capsys.readouterr()
    # Currently returns silently
    assert captured.out == ""


def test_unknown_command_multi_tool(monkeypatch, capsys):
    """Test unknown command with multiple tools registered."""
    @toolable(summary="Tool A")
    def tool_a():
        return "a"

    @toolable(summary="Tool B")
    def tool_b():
        return "b"

    cli = AgentCLI("mycli", tools=[tool_a, tool_b])
    monkeypatch.setattr(sys, "argv", ["mycli", "unknown_cmd", "{}"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "NOT_FOUND"
    assert "unknown_cmd" in response["error"]["message"]


def test_help_flag_no_tools(monkeypatch, capsys):
    """Test --help with no tools registered."""
    cli = AgentCLI("emptycli")
    monkeypatch.setattr(sys, "argv", ["emptycli", "--help"])
    cli.run()

    captured = capsys.readouterr()
    assert "emptycli" in captured.out
    assert "Commands:" in captured.out


def test_tools_flag(monkeypatch, capsys):
    """Test --tools flag."""
    @toolable(summary="Test tool")
    def my_tool():
        return {}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "--tools"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "tools" in data
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "my_tool"


def test_resources_flag(monkeypatch, capsys):
    """Test --resources flag."""
    @resource(uri_pattern="/test/{id}", summary="Test resource")
    def get_resource(id: str):
        return {"id": id}

    cli = AgentCLI("test")
    cli.register_resource(get_resource)

    monkeypatch.setattr(sys, "argv", ["test", "--resources"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "resources" in data
    assert len(data["resources"]) == 1


def test_prompts_flag(monkeypatch, capsys):
    """Test --prompts flag."""
    @prompt(summary="Test prompt", arguments={"x": "Value"})
    def my_prompt(x: str):
        return x

    cli = AgentCLI("test")
    cli.register_prompt(my_prompt)

    monkeypatch.setattr(sys, "argv", ["test", "--prompts"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "prompts" in data
    assert len(data["prompts"]) == 1
