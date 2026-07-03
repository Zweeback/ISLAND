import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error
import sys
import os

# Insert the current directory into sys.path so that local modules can be imported
# even when this test is run via global pytest discovery.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scraper_opendata_dortmund import query_opendata, BASE_URL

class TestScraperOpendataDortmund(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_query_opendata_happy_path_no_params(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "success", "data": []}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = query_opendata("test_endpoint")

        # Verify JSON parsed correctly
        self.assertEqual(res, {"status": "success", "data": []})

        # Verify URL and Headers
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, f"{BASE_URL}/test_endpoint")
        self.assertEqual(req.headers.get("User-agent"), "ZentraleInselAgent/1.0")


    @patch("urllib.request.urlopen")
    def test_query_opendata_happy_path_with_params(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"results": ["a", "b"]}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = query_opendata("search", {"q": "trees", "limit": 5})

        # Verify JSON parsed correctly
        self.assertEqual(res, {"results": ["a", "b"]})

        # Verify URL and Headers
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.full_url, f"{BASE_URL}/search?q=trees&limit=5")
        self.assertEqual(req.headers.get("User-agent"), "ZentraleInselAgent/1.0")

    @patch("urllib.request.urlopen")
    def test_query_opendata_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")

        res = query_opendata("timeout_endpoint")

        self.assertIn("error", res)
        self.assertEqual(res["error"], "<urlopen error Connection timed out>")


    @patch("urllib.request.urlopen")
    def test_query_opendata_invalid_json(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html>Not JSON</html>"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = query_opendata("bad_json_endpoint")

        self.assertIn("error", res)
        # JSONDecodeError string varies slightly between Python versions but generally contains "Expecting value"
        self.assertIn("Expecting value", res["error"])

if __name__ == "__main__":
    unittest.main()
