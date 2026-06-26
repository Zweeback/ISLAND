import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error

# Import the module to be tested
from local_llm_bridge import query_ollama

class TestLocalLLMBridge(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_query_ollama_network_error(self, mock_urlopen):
        # Simulate a network timeout or URL error
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")

        # Call the function
        result_json_str = query_ollama("System prompt", "User prompt")

        # Parse the JSON result
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertTrue(result_dict["error"].startswith("Ollama Call failed: "))
        self.assertIn("Connection timed out", result_dict["error"])

    @patch('urllib.request.urlopen')
    def test_query_ollama_generic_exception(self, mock_urlopen):
        # Simulate a generic exception
        mock_urlopen.side_effect = Exception("Some unknown error")

        # Call the function
        result_json_str = query_ollama("System prompt", "User prompt")

        # Parse the JSON result
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "Ollama Call failed: Some unknown error")

    @patch('urllib.request.urlopen')
    def test_query_ollama_happy_path(self, mock_urlopen):
        # Simulate a successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "content": "Hello there!"
            }
        }).encode('utf-8')
        # Simulate the context manager for urlopen
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the function
        result = query_ollama("System prompt", "User prompt")

        # Assert that it returns the extracted message content
        self.assertEqual(result, "Hello there!")

    @patch('urllib.request.urlopen')
    def test_query_ollama_unexpected_format(self, mock_urlopen):
        # Simulate a response with missing or badly formatted 'message'
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": "This is a string, not a dict"
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Call the function
        result_json_str = query_ollama("System prompt", "User prompt")
        result_dict = json.loads(result_json_str)

        # Assert that it returns the expected error message format
        self.assertIn("error", result_dict)
        self.assertEqual(result_dict["error"], "Unexpected Ollama response format")


if __name__ == '__main__':
    unittest.main()
