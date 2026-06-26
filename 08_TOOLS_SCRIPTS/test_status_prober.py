import pytest
import subprocess
from unittest.mock import patch
from status_prober import get_pid_by_port

# Sample output from netstat -ano
SAMPLE_NETSTAT_OUTPUT = """
Active Connections

  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1234
  TCP    0.0.0.0:8766           0.0.0.0:0              LISTENING       5678
  TCP    127.0.0.1:8421         0.0.0.0:0              LISTENING       9012
  TCP    [::]:135               [::]:0                 LISTENING       1234
  UDP    0.0.0.0:5050           *:*                                    3456
"""

def test_get_pid_by_port_valid():
    with patch('subprocess.check_output') as mock_check_output:
        mock_check_output.return_value = SAMPLE_NETSTAT_OUTPUT.encode('utf-8')

        # Test finding an existing port
        pid = get_pid_by_port(8766)
        assert pid == 5678

        # Test finding another existing port with different local address format
        pid = get_pid_by_port(8421)
        assert pid == 9012

        # Test finding a port that doesn't exist in the output
        pid = get_pid_by_port(9999)
        assert pid is None

        # Ensure subprocess.check_output was called correctly
        mock_check_output.assert_called_with(['netstat', '-ano'])

def test_get_pid_by_port_invalid_port_type():
    # Test with string (vulnerability vector like "8766 | calc.exe")
    pid = get_pid_by_port("8766 | calc.exe")
    assert pid is None

    # Test with float
    pid = get_pid_by_port(8766.0)
    assert pid is None

    # Test with negative integer
    pid = get_pid_by_port(-8766)
    assert pid is None

    # Test with out-of-bounds integer
    pid = get_pid_by_port(70000)
    assert pid is None

def test_get_pid_by_port_subprocess_error():
    with patch('subprocess.check_output') as mock_check_output:
        mock_check_output.side_effect = subprocess.CalledProcessError(1, ['netstat', '-ano'])

        # Should gracefully return None on exception
        pid = get_pid_by_port(8766)
        assert pid is None
