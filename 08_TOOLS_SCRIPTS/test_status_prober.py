import unittest
import socket
from unittest.mock import patch, MagicMock
from status_prober import is_port_open

class TestStatusProber(unittest.TestCase):
    @patch('status_prober.socket.socket')
    def test_is_port_open_success(self, mock_socket_class):
        # Setup the mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

        # When connect is called, it succeeds (returns None)
        mock_socket_instance.connect.return_value = None

        result = is_port_open(8080)

        # Verification
        self.assertTrue(result)
        mock_socket_instance.settimeout.assert_called_once_with(1.0)
        mock_socket_instance.connect.assert_called_once_with(("127.0.0.1", 8080))

    @patch('status_prober.socket.socket')
    def test_is_port_open_connection_refused(self, mock_socket_class):
        # Setup the mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

        # When connect is called, it raises ConnectionRefusedError
        mock_socket_instance.connect.side_effect = ConnectionRefusedError()

        result = is_port_open(8080)

        # Verification
        self.assertFalse(result)
        mock_socket_instance.settimeout.assert_called_once_with(1.0)
        mock_socket_instance.connect.assert_called_once_with(("127.0.0.1", 8080))

    @patch('status_prober.socket.socket')
    def test_is_port_open_timeout(self, mock_socket_class):
        # Setup the mock socket instance
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket_instance

        # When connect is called, it raises socket.timeout
        mock_socket_instance.connect.side_effect = socket.timeout()

        result = is_port_open(8080)

        # Verification
        self.assertFalse(result)
        mock_socket_instance.settimeout.assert_called_once_with(1.0)
        mock_socket_instance.connect.assert_called_once_with(("127.0.0.1", 8080))

if __name__ == '__main__':
    unittest.main()
