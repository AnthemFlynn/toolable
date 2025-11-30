from toolable.errors import ErrorCode, ToolError


def test_error_code_enum():
    """Test ErrorCode enum values."""
    assert ErrorCode.INVALID_INPUT == "INVALID_INPUT"
    assert ErrorCode.TIMEOUT == "TIMEOUT"


def test_error_code_recoverable():
    """Test ErrorCode.recoverable property."""
    # Recoverable errors
    assert ErrorCode.INVALID_INPUT.recoverable is True
    assert ErrorCode.MISSING_PARAM.recoverable is True
    assert ErrorCode.INVALID_PATH.recoverable is True
    assert ErrorCode.NOT_FOUND.recoverable is True
    assert ErrorCode.CONFLICT.recoverable is True
    assert ErrorCode.PRECONDITION.recoverable is True

    # Non-recoverable errors
    assert ErrorCode.TIMEOUT.recoverable is False
    assert ErrorCode.PERMISSION.recoverable is False
    assert ErrorCode.INTERNAL.recoverable is False
    assert ErrorCode.DEPENDENCY.recoverable is False


def test_tool_error_with_error_code():
    """Test ToolError with ErrorCode enum."""
    error = ToolError(ErrorCode.INVALID_INPUT, "Bad input")
    assert error.code == ErrorCode.INVALID_INPUT
    assert error.message == "Bad input"
    assert error.recoverable is True


def test_tool_error_with_string():
    """Test ToolError with string code."""
    error = ToolError("INVALID_INPUT", "Bad input")
    assert error.code == ErrorCode.INVALID_INPUT
    assert error.message == "Bad input"
    assert error.recoverable is True


def test_tool_error_override_recoverable():
    """Test overriding recoverable flag."""
    error = ToolError(ErrorCode.INVALID_INPUT, "Bad input", recoverable=False)
    assert error.recoverable is False


def test_tool_error_with_suggestion():
    """Test ToolError with suggestion."""
    error = ToolError(
        ErrorCode.INVALID_INPUT, "Bad input", suggestion="Try using --help"
    )
    assert error.suggestion == "Try using --help"


def test_tool_error_with_context():
    """Test ToolError with context."""
    error = ToolError(
        ErrorCode.INVALID_INPUT,
        "Bad input",
        context={"field": "email", "value": "invalid"},
    )
    assert error.context == {"field": "email", "value": "invalid"}


def test_tool_error_to_response():
    """Test ToolError.to_response()."""
    error = ToolError(
        ErrorCode.INVALID_INPUT,
        "Bad input",
        suggestion="Try again",
        context={"field": "name"},
    )
    response = error.to_response()

    assert response["status"] == "error"
    assert response["error"]["code"] == "INVALID_INPUT"
    assert response["error"]["message"] == "Bad input"
    assert response["error"]["recoverable"] is True
    assert response["error"]["suggestion"] == "Try again"
    assert response["error"]["context"] == {"field": "name"}
