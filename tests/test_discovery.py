from pydantic import Field

from toolable.decorators import prompt, resource, toolable
from toolable.discovery import (
    extract_schema_from_function,
    generate_prompt_manifest,
    generate_resource_manifest,
    generate_tool_manifest,
)
from toolable.input import ToolInput


def test_extract_schema_from_function_signature():
    """Test schema extraction from function signature."""

    def my_func(name: str, count: int = 5):
        pass

    schema = extract_schema_from_function(my_func)
    assert schema["type"] == "object"
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["count"]["type"] == "integer"
    assert schema["properties"]["count"]["default"] == 5
    assert schema["required"] == ["name"]


def test_extract_schema_with_field_metadata():
    """Test schema extraction with Field() metadata."""

    def my_func(
        name: str = Field(description="User name"),
        age: int = Field(default=0, description="User age"),
    ):
        pass

    schema = extract_schema_from_function(my_func)
    assert schema["properties"]["name"]["description"] == "User name"
    assert schema["properties"]["age"]["description"] == "User age"
    assert schema["properties"]["age"]["default"] == 0


def test_extract_schema_from_input_model():
    """Test schema extraction from ToolInput model."""

    class MyInput(ToolInput):
        name: str = Field(description="User name")
        count: int = 5

    def my_func(input: MyInput):
        pass

    schema = extract_schema_from_function(my_func, input_model=MyInput)
    assert "properties" in schema
    assert "name" in schema["properties"]


def test_extract_schema_complex_types():
    """Test schema extraction with complex types."""

    def my_func(tags: list[str], metadata: dict, active: bool):
        pass

    schema = extract_schema_from_function(my_func)
    assert schema["properties"]["tags"]["type"] == "array"
    assert schema["properties"]["metadata"]["type"] == "object"
    assert schema["properties"]["active"]["type"] == "boolean"


def test_generate_tool_manifest():
    """Test generate_tool_manifest()."""

    @toolable(
        summary="Test tool", examples=[{"name": "test"}], tags=["demo"], streaming=True
    )
    def my_tool(name: str, count: int = 5):
        """This is a test tool."""
        pass

    from toolable.decorators import get_tool_meta

    meta = get_tool_meta(my_tool)
    manifest = generate_tool_manifest(my_tool, meta)

    assert manifest["name"] == "my_tool"
    assert manifest["summary"] == "Test tool"
    assert manifest["description"] == "This is a test tool."
    assert manifest["streaming"] is True
    assert manifest["session_mode"] is False
    assert manifest["examples"] == [{"name": "test"}]
    assert manifest["tags"] == ["demo"]
    assert "schema" in manifest


def test_generate_resource_manifest():
    """Test generate_resource_manifest()."""

    @resource(
        uri_pattern="/files/{file_id}",
        summary="Get file",
        mime_types=["text/plain"],
        tags=["files"],
    )
    def get_file(file_id: str):
        pass

    from toolable.decorators import get_resource_meta

    meta = get_resource_meta(get_file)
    manifest = generate_resource_manifest(get_file, meta)

    assert manifest["uri_pattern"] == "/files/{file_id}"
    assert manifest["summary"] == "Get file"
    assert manifest["mime_types"] == ["text/plain"]
    assert manifest["tags"] == ["files"]


def test_generate_prompt_manifest():
    """Test generate_prompt_manifest()."""

    @prompt(
        summary="Greeting prompt", arguments={"name": "Person name"}, tags=["greetings"]
    )
    def greeting(name: str):
        pass

    from toolable.decorators import get_prompt_meta

    meta = get_prompt_meta(greeting)
    manifest = generate_prompt_manifest(greeting, meta)

    assert manifest["name"] == "greeting"
    assert manifest["summary"] == "Greeting prompt"
    assert manifest["arguments"] == {"name": "Person name"}
    assert manifest["tags"] == ["greetings"]
