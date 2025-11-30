import pytest
from toolable.decorators import (
    toolable,
    resource,
    prompt,
    get_tool_meta,
    get_resource_meta,
    get_prompt_meta,
)
from toolable.input import ToolInput


def test_toolable_decorator_basic():
    """Test @toolable decorator basic usage."""
    @toolable(summary="Test tool")
    def my_tool(name: str):
        return {"message": f"Hello {name}"}

    meta = get_tool_meta(my_tool)
    assert meta is not None
    assert meta["summary"] == "Test tool"
    assert meta["streaming"] is False
    assert meta["session_mode"] is False


def test_toolable_decorator_with_options():
    """Test @toolable with all options."""
    class MyInput(ToolInput):
        name: str

    @toolable(
        summary="Complex tool",
        input_model=MyInput,
        examples=[{"name": "test"}],
        tags=["demo", "test"],
        streaming=True,
        session_mode=False,
    )
    def my_tool(input: MyInput):
        return {"message": input.name}

    meta = get_tool_meta(my_tool)
    assert meta["summary"] == "Complex tool"
    assert meta["input_model"] == MyInput
    assert meta["examples"] == [{"name": "test"}]
    assert meta["tags"] == ["demo", "test"]
    assert meta["streaming"] is True
    assert meta["session_mode"] is False


def test_toolable_preserves_function():
    """Test that @toolable preserves function behavior."""
    @toolable(summary="Test")
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5
    assert add.__name__ == "add"


def test_resource_decorator():
    """Test @resource decorator."""
    @resource(
        uri_pattern="/files/{file_id}",
        summary="Get file by ID",
        mime_types=["text/plain"],
        tags=["files"]
    )
    def get_file(file_id: str):
        return {"id": file_id, "content": "..."}

    meta = get_resource_meta(get_file)
    assert meta is not None
    assert meta["uri_pattern"] == "/files/{file_id}"
    assert meta["summary"] == "Get file by ID"
    assert meta["mime_types"] == ["text/plain"]
    assert meta["tags"] == ["files"]


def test_prompt_decorator():
    """Test @prompt decorator."""
    @prompt(
        summary="Generate greeting",
        arguments={"name": "Person name", "style": "Greeting style"},
        tags=["greetings"]
    )
    def greeting_prompt(name: str, style: str) -> str:
        return f"Generate a {style} greeting for {name}"

    meta = get_prompt_meta(greeting_prompt)
    assert meta is not None
    assert meta["summary"] == "Generate greeting"
    assert meta["arguments"] == {"name": "Person name", "style": "Greeting style"}
    assert meta["tags"] == ["greetings"]


def test_get_meta_on_undecorated_function():
    """Test get_*_meta on undecorated functions."""
    def regular_function():
        pass

    assert get_tool_meta(regular_function) is None
    assert get_resource_meta(regular_function) is None
    assert get_prompt_meta(regular_function) is None


def test_multiple_decorated_functions():
    """Test multiple decorated functions don't interfere."""
    @toolable(summary="Tool A")
    def tool_a():
        return "a"

    @toolable(summary="Tool B")
    def tool_b():
        return "b"

    meta_a = get_tool_meta(tool_a)
    meta_b = get_tool_meta(tool_b)

    assert meta_a["summary"] == "Tool A"
    assert meta_b["summary"] == "Tool B"
