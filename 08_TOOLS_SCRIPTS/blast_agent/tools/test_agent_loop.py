import json
import urllib.request
from unittest.mock import MagicMock, patch

from agent_loop import call_llm

def test_call_llm_success():
    """Test the happy path where the LLM API returns a valid response."""
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "This is a mock response from the LLM."
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    assert result == "This is a mock response from the LLM."

def test_call_llm_unexpected_format_missing_choices():
    """Test the case where the LLM API returns a response missing 'choices'."""
    mock_response_data = {
        "not_choices": []
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    expected_error = json.dumps({"error": "Unexpected LLM response format"})
    assert result == expected_error

def test_call_llm_unexpected_format_empty_choices():
    """Test the case where the LLM API returns a response with an empty 'choices' list."""
    mock_response_data = {
        "choices": []
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    expected_error = json.dumps({"error": "Unexpected LLM response format"})
    assert result == expected_error

def test_call_llm_unexpected_format_missing_message():
    """Test the case where the LLM API returns a response where the first choice is missing 'message'."""
    mock_response_data = {
        "choices": [
            {
                "not_message": {
                    "content": "This shouldn't be reached."
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    assert result == ""

def test_call_llm_unexpected_format_missing_content():
    """Test the case where the LLM API returns a response where the message is missing 'content'."""
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "not_content": "This shouldn't be reached."
                }
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")

    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_urlopen):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    # As per original code, `message.get("content", "")` returns `""` if missing
    assert result == ""

def test_call_llm_exception_handling():
    """Test the case where an exception is raised during the HTTP request."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection Error")):
        result = call_llm("dummy_api_key", "system_prompt", "user_prompt")

    expected_error = json.dumps({"error": "LLM Call failed: Connection Error"})
    assert result == expected_error
