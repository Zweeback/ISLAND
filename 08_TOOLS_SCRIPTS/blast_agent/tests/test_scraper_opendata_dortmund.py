import pytest
from unittest.mock import patch
import os
import sys

# Ensure module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.scraper_opendata_dortmund import query_opendata

@patch('urllib.request.urlopen')
def test_query_opendata_error_handling(mock_urlopen):
    # Setup mock to raise Exception
    error_msg = "test error"
    mock_urlopen.side_effect = Exception(error_msg)

    # Call the function
    result = query_opendata("test_endpoint")

    # Verify result
    assert "error" in result
    assert result["error"] == error_msg
