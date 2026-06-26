import unittest
from unittest.mock import patch, MagicMock
import socket
import status_prober

class TestStatusProber(unittest.TestCase):
    def setUp(self):
        # Reset the cache before each test
        status_prober._PORT_TO_PID_CACHE = None

    @patch('subprocess.check_output')
    def test_get_pid_by_port(self, mock_check_output):
        # Mock netstat output
        mock_output = b"""
  Proto  Local Address          Foreign Address        State           PID
  TCP    127.0.0.1:8766         0.0.0.0:0              LISTENING       1234
  TCP    127.0.0.1:8421         0.0.0.0:0              LISTENING       5678
"""
        mock_check_output.return_value = mock_output

        # First call should execute subprocess and populate cache
        pid1 = status_prober.get_pid_by_port(8766)
        self.assertEqual(pid1, 1234)
        mock_check_output.assert_called_once()

        # Second call should use cache, mock should NOT be called again
        pid2 = status_prober.get_pid_by_port(8421)
        self.assertEqual(pid2, 5678)
        mock_check_output.assert_called_once()

        # Test non-existent port
        pid3 = status_prober.get_pid_by_port(9999)
        self.assertIsNone(pid3)
        mock_check_output.assert_called_once()

    @patch('socket.socket')
    def test_is_port_open_success(self, mock_socket_class):
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

        # connect does not raise exception, meaning port is open
        self.assertTrue(status_prober.is_port_open(8080))
        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 8080))

    @patch('socket.socket')
    def test_is_port_open_failure(self, mock_socket_class):
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

        # connect raises exception, meaning port is closed
        mock_socket_instance.connect.side_effect = ConnectionRefusedError()
        self.assertFalse(status_prober.is_port_open(8080))

if __name__ == '__main__':
    unittest.main()
