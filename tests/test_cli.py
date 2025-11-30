import json
import sys

import pytest
from pydantic import Field

from toolable.cli import AgentCLI
from toolable.decorators import prompt, resource, toolable
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


# Task 11: Resource Fetching End-to-End Tests
def test_fetch_resource_success(monkeypatch, capsys):
    """Test successful resource fetch."""
    @resource(uri_pattern="/files/{file_id}", summary="Get file")
    def get_file(file_id: str):
        return {"id": file_id, "content": f"Content of {file_id}"}

    cli = AgentCLI("test")
    cli.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["test", "--resource", "/files/123"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["id"] == "123"
    assert "Content of 123" in data["content"]


def test_fetch_resource_not_found(monkeypatch, capsys):
    """Test resource fetch with no matching pattern."""
    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id}

    cli = AgentCLI("test")
    cli.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["test", "--resource", "/users/123"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["status"] == "error"
    assert data["error"]["code"] == "NOT_FOUND"


# Task 12: Prompt Rendering Tests
def test_render_prompt_success(monkeypatch, capsys):
    """Test successful prompt rendering."""
    @prompt(summary="Greeting", arguments={"name": "Name"})
    def greet(name: str):
        return f"Hello {name}!"

    cli = AgentCLI("test")
    cli.register_prompt(greet)

    monkeypatch.setattr(sys, "argv", ["test", "--prompt", "greet", '{"name": "Alice"}'])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data == "Hello Alice!"


def test_render_prompt_not_found(monkeypatch, capsys):
    """Test rendering unknown prompt."""
    cli = AgentCLI("test")

    monkeypatch.setattr(sys, "argv", ["test", "--prompt", "unknown", "{}"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["status"] == "error"
    assert data["error"]["code"] == "NOT_FOUND"


# Task 17: Duplicate Flags Test
def test_duplicate_flags_last_wins(monkeypatch, capsys):
    """Test that duplicate flags - last value wins."""
    @toolable(summary="Echo")
    def echo(message: str):
        return {"message": message}

    cli = AgentCLI(echo)
    monkeypatch.setattr(sys, "argv", ["echo", "--message", "first", "--message", "second"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    # Document current behavior (last wins)
    assert response["result"]["message"] == "second"


# Task 18: Type Coercion Tests
def test_flag_json_array_parsing(monkeypatch, capsys):
    """Test that JSON arrays in flag values are parsed."""
    @toolable(summary="Process")
    def process(items: list):
        return {"count": len(items)}

    cli = AgentCLI(process)
    monkeypatch.setattr(sys, "argv", ["process", "--items", '["a", "b", "c"]'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["result"]["count"] == 3


def test_flag_invalid_json_treated_as_string(monkeypatch, capsys):
    """Test that invalid JSON in flags is treated as string."""
    @toolable(summary="Echo")
    def echo(message: str):
        return {"message": message}

    cli = AgentCLI(echo)
    # Use a string value that doesn't start with { to test fallback to string
    monkeypatch.setattr(sys, "argv", ["echo", "--message", "[invalid"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    # Invalid JSON becomes string literal
    assert response["result"]["message"] == "[invalid"


# Task 13: Validate Flag Test
def test_validate_flag_with_pre_validate_error(monkeypatch, capsys):
    """Test --validate catches pre_validate errors."""
    from toolable.errors import ErrorCode, ToolError

    class MyInput(ToolInput):
        email: str

        def pre_validate(self):
            if "@" not in self.email:
                raise ToolError(ErrorCode.INVALID_INPUT, "Invalid email format")

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        return {}

    cli = AgentCLI(my_tool)
    monkeypatch.setattr(sys, "argv", ["my_tool", "--validate", '{"email": "invalid"}'])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["valid"] is False
    assert "errors" in data


# Task 14: Single-Tool Mode Fallback Test
def test_single_tool_mode_fallback(monkeypatch, capsys):
    """Test single-tool mode when command doesn't match tool name."""
    @toolable(summary="Only tool")
    def only_tool(value: str):
        return {"value": value}

    cli = AgentCLI("mycli", tools=[only_tool])

    # Args don't start with "only_tool" but there's only one tool
    monkeypatch.setattr(sys, "argv", ["mycli", '{"value": "test"}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["value"] == "test"


# Task 21: Tool-Specific Help Test
def test_tool_help_output(monkeypatch, capsys):
    """Test tool-specific --help output."""
    class MyInput(ToolInput):
        name: str = Field(description="User name")
        age: int = Field(default=18, description="User age")

    @toolable(summary="Create user", input_model=MyInput)
    def create_user(input: MyInput):
        """Create a new user in the system."""
        return {}

    cli = AgentCLI(create_user)
    monkeypatch.setattr(sys, "argv", ["create_user", "--help"])
    cli.run()

    captured = capsys.readouterr()

    # Verify help contains key elements
    assert "create_user" in captured.out
    assert "Create user" in captured.out
    assert "Usage:" in captured.out
    assert "Commands:" in captured.out
    # Verify the summary is shown
    assert "Create user" in captured.out


def test_register_non_resource_function(capsys):
    """Test registering a function without @resource decorator raises ValueError."""
    def not_a_resource():
        return {}

    cli = AgentCLI("test")

    with pytest.raises(ValueError, match="is not decorated with @resource"):
        cli.register_resource(not_a_resource)


def test_tool_args_when_command_matches(monkeypatch, capsys):
    """Test tool_args is set correctly when command matches tool name."""
    @toolable(summary="Test")
    def my_tool(value: str):
        return {"value": value}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", "--value", "hello"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["value"] == "hello"


def test_json_decode_error_in_tool_execution(monkeypatch, capsys):
    """Test JSON decode error handling in tool execution."""
    @toolable(summary="Test")
    def my_tool(value: str):
        return {"value": value}

    cli = AgentCLI("test", tools=[my_tool])
    # Pass invalid JSON
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", "{invalid json}"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert "Invalid JSON" in response["error"]["message"]


def test_pre_validate_error_handling(monkeypatch, capsys):
    """Test pre_validate error is caught and returned."""
    from toolable.errors import ErrorCode, ToolError

    class MyInput(ToolInput):
        value: str

        def pre_validate(self):
            if self.value == "bad":
                raise ToolError(ErrorCode.INVALID_INPUT, "Bad value")

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        return {}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", '{"value": "bad"}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert "Bad value" in response["error"]["message"]


def test_working_dir_changes_directory(monkeypatch, capsys, tmp_path):
    """Test working_dir changes current directory."""
    import os

    class MyInput(ToolInput):
        working_dir: str | None = None

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        return {"cwd": os.getcwd()}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", json.dumps({"working_dir": str(tmp_path)})])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert tmp_path.name in response["result"]["cwd"]


def test_response_already_has_status(monkeypatch, capsys):
    """Test that response with status key is not wrapped."""
    @toolable(summary="Test")
    def my_tool():
        return {"status": "custom", "data": "value"}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    # Should be returned as-is without wrapping
    assert response["status"] == "custom"
    assert response["data"] == "value"


def test_parse_input_with_input_model_from_flags(monkeypatch, capsys):
    """Test parsing CLI flags into input model."""
    class MyInput(ToolInput):
        name: str
        count: int

    @toolable(summary="Test", input_model=MyInput)
    def my_tool(input: MyInput):
        return {"name": input.name, "count": input.count}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", "--name", "test", "--count", "5"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["name"] == "test"
    assert response["result"]["count"] == 5


def test_discover_with_resources_and_prompts(monkeypatch, capsys):
    """Test _print_discover includes resources and prompts."""
    @toolable(summary="Tool")
    def my_tool():
        return {}

    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id}

    @prompt(summary="Greet", arguments={"name": "Name"})
    def greet(name: str):
        return f"Hello {name}"

    cli = AgentCLI("test", tools=[my_tool])
    cli.register_resource(get_file)
    cli.register_prompt(greet)

    monkeypatch.setattr(sys, "argv", ["test", "--discover"])
    cli.run()

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert len(data["tools"]) == 1
    assert len(data["resources"]) == 1
    assert len(data["prompts"]) == 1
    assert data["resources"][0]["uri_pattern"] == "/files/{id}"
    assert data["prompts"][0]["name"] == "greet"


def test_fetch_resource_with_exception(monkeypatch, capsys):
    """Test resource fetch handles exceptions."""
    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        raise RuntimeError("Database error")

    cli = AgentCLI("test")
    cli.register_resource(get_file)

    monkeypatch.setattr(sys, "argv", ["test", "--resource", "/files/123"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INTERNAL"
    assert "Database error" in response["error"]["message"]


def test_render_prompt_with_exception(monkeypatch, capsys):
    """Test prompt render handles exceptions."""
    @prompt(summary="Test", arguments={"x": "Value"})
    def my_prompt(x: str):
        raise ValueError("Invalid template")

    cli = AgentCLI("test")
    cli.register_prompt(my_prompt)

    monkeypatch.setattr(sys, "argv", ["test", "--prompt", "my_prompt", '{"x": "value"}'])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INTERNAL"
    assert "Invalid template" in response["error"]["message"]


def test_validate_input_generic_exception(monkeypatch, capsys):
    """Test _validate_input handles generic exceptions."""
    @toolable(summary="Test")
    def my_tool(value: str):
        return {}

    cli = AgentCLI("test", tools=[my_tool])
    # Pass malformed JSON to trigger generic exception
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", "--validate", "not json at all"])
    cli.run()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert result["valid"] is False
    assert "errors" in result


def test_print_tool_help_with_docstring(monkeypatch, capsys):
    """Test _print_tool_help displays function docstring and parameters."""
    class MyInput(ToolInput):
        name: str = Field(description="User name")
        count: int = Field(default=10, description="Number of items")

    @toolable(summary="Process data", input_model=MyInput)
    def process_data(input: MyInput):
        """Process data with the given parameters.

        This is a detailed description of what the function does.
        """
        return {}

    cli = AgentCLI("test", tools=[process_data])
    monkeypatch.setattr(sys, "argv", ["test", "process_data", "--help"])
    cli.run()

    captured = capsys.readouterr()

    # Check that help output contains expected elements
    assert "process_data" in captured.out
    assert "Process data" in captured.out
    assert "Process data with the given parameters" in captured.out
    assert "Parameters:" in captured.out
    assert "--name" in captured.out
    assert "--count" in captured.out
    assert "default: 10" in captured.out


def test_tool_returns_non_dict_non_response(monkeypatch, capsys):
    """Test tool returning a non-dict value (like a string or int)."""
    @toolable(summary="Return string")
    def my_tool():
        return "plain string result"

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["result"] == "plain string result"


def test_parse_input_flag_without_value_at_end(monkeypatch, capsys):
    """Test parsing flag at end of arguments without a value."""
    @toolable(summary="Test")
    def my_tool(verbose: bool = False):
        return {"verbose": verbose}

    cli = AgentCLI("test", tools=[my_tool])
    monkeypatch.setattr(sys, "argv", ["test", "my_tool", "--verbose"])
    cli.run()

    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert response["status"] == "success"
    assert response["result"]["verbose"] is True
