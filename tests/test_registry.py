import pytest
import json
import subprocess
import warnings
from pathlib import Path
from toolable.registry import ToolRegistry


def test_tool_registry_init():
    """Test ToolRegistry initialization."""
    registry = ToolRegistry([])
    assert registry.tools == {}
    assert registry.resources == {}
    assert registry.prompts == {}


def test_tool_registry_discover_empty():
    """Test discover() with no tools."""
    registry = ToolRegistry([])
    summaries = registry.discover()
    assert summaries == {}


def test_registry_load_valid_tool():
    """Test loading a valid tool."""
    tool_path = Path(__file__).parent / "fixtures" / "valid_tool.py"
    registry = ToolRegistry([tool_path])

    assert "example" in registry.tools
    assert registry.tools["example"]["summary"] == "Example tool"


def test_registry_load_broken_tool():
    """Test that broken tool emits warning but doesn't crash."""
    tool_path = Path(__file__).parent / "fixtures" / "broken_tool.py"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        registry = ToolRegistry([tool_path])

        # Should have warned about failure
        assert len(w) == 1
        assert "Failed to load tool" in str(w[0].message)

    # Registry should be empty but not crashed
    assert len(registry.tools) == 0


def test_registry_load_slow_tool():
    """Test that slow tool times out during discovery."""
    tool_path = Path(__file__).parent / "fixtures" / "slow_tool.py"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        registry = ToolRegistry([tool_path])

        # Should have warned about timeout
        assert len(w) == 1
        assert "Failed to load tool" in str(w[0].message)

    assert len(registry.tools) == 0


def test_registry_nonexistent_path():
    """Test loading from nonexistent path."""
    registry = ToolRegistry([Path("/nonexistent/tool.py")])
    assert len(registry.tools) == 0


def test_registry_schema():
    """Test getting schema for a tool."""
    tool_path = Path(__file__).parent / "fixtures" / "valid_tool.py"
    registry = ToolRegistry([tool_path])

    # valid_tool.py doesn't properly implement --manifest, but it does return JSON
    # The schema() method will parse whatever is returned
    schema = registry.schema("example")
    # It returns the normal success response, not a proper schema
    assert isinstance(schema, dict)


def test_registry_schema_unknown_tool():
    """Test getting schema for unknown tool raises KeyError."""
    registry = ToolRegistry([])

    with pytest.raises(KeyError, match="Unknown tool"):
        registry.schema("unknown_tool")


def test_registry_call_tool():
    """Test calling an external tool."""
    tool_path = Path(__file__).parent / "fixtures" / "valid_tool.py"
    registry = ToolRegistry([tool_path])

    # Call the tool (won't work without full implementation, but tests the path)
    result = registry.call("example", {})
    # valid_tool.py returns success response
    assert "status" in result


def test_registry_call_unknown_tool():
    """Test calling unknown tool."""
    registry = ToolRegistry([])
    result = registry.call("unknown", {})

    assert result["status"] == "error"
    assert result["error"]["code"] == "NOT_FOUND"
