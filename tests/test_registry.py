import pytest
import json
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


# Note: Full testing of ToolRegistry would require creating
# executable test tools, which is better suited for integration tests
