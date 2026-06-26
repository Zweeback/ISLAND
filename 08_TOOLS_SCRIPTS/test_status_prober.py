import unittest
from unittest.mock import patch
import subprocess

from status_prober import get_pid_by_port

class TestGetPidByPort(unittest.TestCase):
    @patch('subprocess.check_output')
    def test_get_pid_by_port_success(self, mock_check_output):
        # Mock netstat output
        mock_output = b"  TCP    127.0.0.1:8766         0.0.0.0:0              LISTENING       1234\r\n"
        mock_check_output.return_value = mock_output

        pid = get_pid_by_port(8766)
        self.assertEqual(pid, 1234)

    @patch('subprocess.check_output')
    def test_get_pid_by_port_exception(self, mock_check_output):
        # Mock check_output to raise CalledProcessError
        mock_check_output.side_effect = subprocess.CalledProcessError(1, 'cmd')

        pid = get_pid_by_port(8766)
        self.assertIsNone(pid)

    @patch('subprocess.check_output')
    def test_get_pid_by_port_malformed_output(self, mock_check_output):
        # Mock check_output with malformed output
        mock_output = b"some random output that doesn't match\r\n"
        mock_check_output.return_value = mock_output

        pid = get_pid_by_port(8766)
        self.assertIsNone(pid)

    @patch('subprocess.check_output')
    def test_get_pid_by_port_no_port_match(self, mock_check_output):
        # Mock check_output where the port doesn't end with :port
        mock_output = b"  TCP    127.0.0.1:87665        0.0.0.0:0              LISTENING       1234\r\n"
        mock_check_output.return_value = mock_output

        pid = get_pid_by_port(8766)
        self.assertIsNone(pid)

if __name__ == '__main__':
    unittest.main()
