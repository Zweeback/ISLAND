import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error
import sys
import os

# Insert the current directory into sys.path so that local modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the module to be tested
from agent_loop import call_llm

class TestCallLLM(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_call_llm_success(self, mock_urlopen):
        # Simulate a successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": "Success!"
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the function
        result = call_llm("test_key", "System prompt", "User prompt")

        # Assert that it returns the extracted message content
        self.assertEqual(result, "Success!")

    @patch('urllib.request.urlopen')
    def test_call_llm_unexpected_format(self, mock_urlopen):
        # Simulate a response with unexpected format
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "not_message": {
                    "content": "foo"
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the function
        result_json_str = call_llm("test_key", "System prompt", "User prompt")
        # In case of missing 'content' returning from a dict without 'message', the function actually returns 'Unexpected LLM response format'
        # BUT wait! If 'message' key is not there, `first_choice.get("message", {})` returns `{}`.
        # Then `isinstance(message, dict)` is True.
        # Then `content = message.get("content", "")` returns `""`.
        # Then `return str(content)` returns `""`.
        # So it doesn't return the "error" JSON!

        self.assertEqual(result_json_str, "")

    @patch('urllib.request.urlopen')
    def test_call_llm_unexpected_format_2(self, mock_urlopen):
        # Simulate a response with no choices
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "not_choices": []
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the function
        result_json_str = call_llm("test_key", "System prompt", "User prompt")
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "Unexpected LLM response format")

    @patch('urllib.request.urlopen')
    def test_call_llm_network_error(self, mock_urlopen):
        # Simulate a network timeout or URL error
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")

        # Call the function
        result_json_str = call_llm("test_key", "System prompt", "User prompt")
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertTrue(result_dict["error"].startswith("LLM Call failed: <urlopen error Connection timed out>"))

    @patch('urllib.request.urlopen')
    def test_call_llm_generic_exception(self, mock_urlopen):
        # Simulate a generic exception
        mock_urlopen.side_effect = Exception("Some unknown error")

        # Call the function
        result_json_str = call_llm("test_key", "System prompt", "User prompt")
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "LLM Call failed: Some unknown error")


if __name__ == '__main__':
    unittest.main()
