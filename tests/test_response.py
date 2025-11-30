from toolable.response import Response


def test_success_response():
    """Test Response.success()."""
    result = Response.success({"message": "Done", "count": 5})
    assert result == {
        "status": "success",
        "result": {"message": "Done", "count": 5}
    }


def test_error_response_minimal():
    """Test Response.error() with minimal params."""
    result = Response.error("NOT_FOUND", "File not found")
    assert result == {
        "status": "error",
        "error": {
            "code": "NOT_FOUND",
            "message": "File not found",
            "recoverable": False,
        }
    }


def test_error_response_with_suggestion():
    """Test Response.error() with suggestion."""
    result = Response.error(
        "INVALID_INPUT",
        "Bad email",
        recoverable=True,
        suggestion="Use format: user@example.com"
    )
    assert result["error"]["suggestion"] == "Use format: user@example.com"


def test_error_response_with_context():
    """Test Response.error() with context."""
    result = Response.error(
        "INVALID_INPUT",
        "Bad value",
        context={"field": "age", "value": -5}
    )
    assert result["error"]["context"] == {"field": "age", "value": -5}


def test_partial_response_all_success():
    """Test Response.partial() when all operations succeed."""
    result = Response.partial(
        {"items": [1, 2, 3]},
        []
    )
    assert result["status"] == "success"
    assert result["summary"]["succeeded"] == 3
    assert result["summary"]["failed"] == 0


def test_partial_response_all_failure():
    """Test Response.partial() when all operations fail."""
    errors = [
        {"code": "NOT_FOUND", "message": "Item 1 not found", "recoverable": True},
        {"code": "NOT_FOUND", "message": "Item 2 not found", "recoverable": True},
    ]
    result = Response.partial({}, errors)
    assert result["status"] == "error"
    assert result["summary"]["succeeded"] == 0
    assert result["summary"]["failed"] == 2


def test_partial_response_mixed():
    """Test Response.partial() with mixed success/failure."""
    errors = [
        {"code": "NOT_FOUND", "message": "Item 3 not found", "recoverable": True},
    ]
    result = Response.partial(
        {"items": [1, 2]},
        errors
    )
    assert result["status"] == "partial"
    assert result["summary"]["succeeded"] == 2
    assert result["summary"]["failed"] == 1
    assert result["summary"]["recoverable_failures"] == 1


def test_partial_response_with_result_key():
    """Test Response.partial() with explicit result_key."""
    result = Response.partial(
        {"created": [1, 2, 3], "metadata": {"total": 5}},
        [],
        result_key="created"
    )
    assert result["summary"]["succeeded"] == 3


def test_partial_response_auto_detect_result_key():
    """Test Response.partial() auto-detecting result key."""
    result = Response.partial(
        {"items": [1, 2]},
        []
    )
    assert result["summary"]["succeeded"] == 2
