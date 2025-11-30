import pytest
from pydantic import Field, ValidationError

from toolable.errors import ToolError
from toolable.input import ToolInput


def test_tool_input_basic():
    """Test basic ToolInput functionality."""
    class MyInput(ToolInput):
        name: str
        count: int = 5

    input_obj = MyInput(name="test")
    assert input_obj.name == "test"
    assert input_obj.count == 5


def test_tool_input_forbid_extra():
    """Test that extra fields are forbidden."""
    class MyInput(ToolInput):
        name: str

    with pytest.raises(ValidationError):
        MyInput(name="test", extra_field="value")


def test_tool_input_context():
    """Test context() method."""
    class MyInput(ToolInput):
        name: str

        def context(self):
            return {"source": "test"}

    input_obj = MyInput(name="test")
    assert input_obj.context() == {"source": "test"}


def test_tool_input_pre_validate():
    """Test pre_validate() hook."""
    class MyInput(ToolInput):
        email: str

        def pre_validate(self):
            if "@" not in self.email:
                raise ToolError(
                    "INVALID_INPUT",
                    "Email must contain @",
                    suggestion="Use format: user@example.com"
                )

    input_obj = MyInput(email="user@example.com")
    input_obj.pre_validate()  # Should not raise

    input_obj_bad = MyInput(email="invalid")
    with pytest.raises(ToolError) as exc_info:
        input_obj_bad.pre_validate()
    assert exc_info.value.code.value == "INVALID_INPUT"


def test_tool_input_to_log_safe():
    """Test to_log_safe() method."""
    class MyInput(ToolInput):
        username: str
        password: str

        def to_log_safe(self):
            data = self.model_dump()
            data["password"] = "***REDACTED***"
            return data

    input_obj = MyInput(username="admin", password="secret123")
    safe_data = input_obj.to_log_safe()
    assert safe_data["username"] == "admin"
    assert safe_data["password"] == "***REDACTED***"


def test_tool_input_reserved_fields():
    """Test reserved field names."""
    class MyInput(ToolInput):
        name: str
        working_dir: str | None = None
        timeout: int | None = None
        dry_run: bool = False
        verbose: bool = False

    input_obj = MyInput(
        name="test",
        working_dir="/tmp",
        timeout=30,
        dry_run=True,
        verbose=True
    )
    assert input_obj.working_dir == "/tmp"
    assert input_obj.timeout == 30
    assert input_obj.dry_run is True
    assert input_obj.verbose is True


def test_tool_input_with_field_metadata():
    """Test ToolInput with Field() metadata."""
    class MyInput(ToolInput):
        name: str = Field(description="User name")
        age: int = Field(default=0, description="User age")

    input_obj = MyInput(name="Alice")
    assert input_obj.name == "Alice"
    assert input_obj.age == 0
