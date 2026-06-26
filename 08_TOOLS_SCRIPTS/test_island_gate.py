import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from datetime import datetime, timezone, timedelta
from island_gate import parse_time

class TestParseTime(unittest.TestCase):
    def test_parse_valid_iso_string(self):
        dt = parse_time("2023-10-25T14:30:00")
        self.assertEqual(dt, datetime(2023, 10, 25, 14, 30, 0))

    def test_parse_valid_iso_string_with_z(self):
        dt = parse_time("2023-10-25T14:30:00Z")
        self.assertEqual(dt, datetime(2023, 10, 25, 14, 30, 0, tzinfo=timezone.utc))

    def test_parse_valid_iso_string_with_offset(self):
        dt = parse_time("2023-10-25T14:30:00+02:00")
        self.assertEqual(dt, datetime(2023, 10, 25, 14, 30, 0, tzinfo=timezone(timedelta(hours=2))))

    def test_parse_invalid_string(self):
        dt = parse_time("invalid-date")
        self.assertIsNone(dt)

    def test_parse_empty_string(self):
        dt = parse_time("")
        self.assertIsNone(dt)

    def test_parse_none(self):
        dt = parse_time(None)
        self.assertIsNone(dt)

    def test_parse_wrong_type(self):
        dt = parse_time(123)
        self.assertIsNone(dt)
        dt = parse_time({"date": "2023-10-25"})
        self.assertIsNone(dt)

if __name__ == '__main__':
    unittest.main()
