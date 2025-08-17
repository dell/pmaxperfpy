import sys
import unittest
from unittest.mock import Mock
import PyU4V

sys.path.append('app')
import pmaxperf

cfg = {
    'hostname': 'local',
    'username': 'user',
    'password': 'secret',
    'unisphere_port': 1234,
    'verify': True
}

class ConfigTests(unittest.TestCase):

    def test_connection(self):
        PyU4V.U4VConn = Mock()
        PyU4V.U4VConn.return_value = "call_ok"
        self.assertEqual(pmaxperf.connect_unisphere(cfg), "call_ok")
        PyU4V.U4VConn.assert_called_once()
