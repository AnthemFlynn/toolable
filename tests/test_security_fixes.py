import pytest
import re
from toolable.cli import AgentCLI
from toolable.decorators import toolable, resource


def test_resource_uri_escaping():
    """Test that resource URI patterns properly escape literal characters."""
    @resource(uri_pattern="/files/{id}.json", summary="Get JSON file")
    def get_json_file(id: str):
        return {"id": id, "content": "data"}

    cli = AgentCLI("test")
    cli.register_resource(get_json_file)

    # Build the regex pattern the same way the code does
    pattern = "/files/{id}.json"
    temp_pattern = re.sub(r"\{(\w+)\}", "\x00\\1\x00", pattern)
    escaped = re.escape(temp_pattern)
    regex_pattern = re.sub(r"\x00(\w+)\x00", r"(?P<\1>[^/]+)", escaped)

    # Should match exact pattern
    assert re.fullmatch(regex_pattern, "/files/123.json")

    # Should NOT match with wrong extension (. is escaped)
    assert not re.fullmatch(regex_pattern, "/files/123Xjson")

    # Should NOT match with extra trailing content
    assert not re.fullmatch(regex_pattern, "/files/123.json/extra")


def test_resource_uri_anchoring():
    """Test that resource URI patterns require exact matches."""
    @resource(uri_pattern="/files/{id}", summary="Get file")
    def get_file(id: str):
        return {"id": id}

    cli = AgentCLI("test")
    cli.register_resource(get_file)

    pattern = "/files/{id}"
    temp_pattern = re.sub(r"\{(\w+)\}", "\x00\\1\x00", pattern)
    escaped = re.escape(temp_pattern)
    regex_pattern = re.sub(r"\x00(\w+)\x00", r"(?P<\1>[^/]+)", escaped)

    # Should match exact pattern
    assert re.fullmatch(regex_pattern, "/files/123")

    # Should NOT match with extra path segments
    assert not re.fullmatch(regex_pattern, "/files/123/extra")


def test_streaming_mode_required_flag(monkeypatch, capsys):
    """Test that streaming tools require --stream flag."""
    import sys

    @toolable(summary="Stream test", streaming=True)
    def stream_tool():
        yield {"type": "progress", "message": "test"}

    cli = AgentCLI(stream_tool)

    # Without --stream flag, should get clear error
    monkeypatch.setattr(sys, "argv", ["stream_tool", "{}"])
    cli.run()

    captured = capsys.readouterr()
    import json
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert "--stream" in response["error"]["message"]
    assert response["error"]["suggestion"] == "Add --stream to the command"


def test_session_mode_required_flag(monkeypatch, capsys):
    """Test that session tools require --session flag."""
    import sys

    @toolable(summary="Session test", session_mode=True)
    def session_tool():
        yield {"type": "session_start", "message": "test"}

    cli = AgentCLI(session_tool)

    # Without --session flag, should get clear error
    monkeypatch.setattr(sys, "argv", ["session_tool", "{}"])
    cli.run()

    captured = capsys.readouterr()
    import json
    response = json.loads(captured.out)

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert "--session" in response["error"]["message"]
    assert response["error"]["suggestion"] == "Add --session to the command"
