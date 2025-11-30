import pytest
from toolable.sampling import configure_sampling, _sample_config


def test_configure_sampling_stdin():
    """Test configure_sampling() with stdin."""
    configure_sampling("stdin")
    assert _sample_config["via"] == "stdin"


def test_configure_sampling_http():
    """Test configure_sampling() with HTTP URL."""
    configure_sampling("http://localhost:8000/sample")
    assert _sample_config["via"] == "http://localhost:8000/sample"


def test_sample_config_default():
    """Test default sample config."""
    # Reset to default
    configure_sampling("stdin")
    assert _sample_config["via"] == "stdin"


# Note: Full testing of sample() would require mocking stdin/HTTP
# Integration tests would cover the actual protocol
