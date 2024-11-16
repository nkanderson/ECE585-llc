import unittest
from unittest.mock import MagicMock, patch
from common.constants import LogLevel

from utils.event_handler import handle_event


class TestEventHandler(unittest.TestCase):
    def setUp(self):
        # Expected initial cache stats dictionary
        self.expected_cache_stats = {
            "cache_reads": 0,
            "cache_writes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Mocking the config logger and args for testing
        self.mock_logger = MagicMock()
        self.mock_args = MagicMock(silent=False, debug=True)

        # Patch the config logger and args
        patch(
            "config.project_config.config.get_logger", return_value=self.mock_logger
        ).start()
        patch(
            "config.project_config.config.get_args", return_value=self.mock_args
        ).start()

    def tearDown(self):
        # Stop any patches done during the test
        patch.stopall()

    def test_handle_event_returns_initial_cache_stats(self):
        """Test that handle_event returns the correct initial cache stats for each opcode."""

        # Test for all valid opcodes (0-9, excluding 7 which isn't handled)
        for opcode in [0, 1, 2, 3, 4, 5, 6, 8, 9]:
            with self.subTest(opcode=opcode):
                # result = self.handle_event(opcode)
                result = handle_event(opcode)
                self.assertEqual(result, self.expected_cache_stats)

    def test_handle_event_write_from_l1(self):
        """Test that handle_event with opcode 1 returns expected cache stats and logs the correct message."""

        result = handle_event(1)

        # For now, still returning initial cache stats
        # This check can be updated when different stats are returned
        self.assertEqual(result, self.expected_cache_stats)

        # Verify logger called with correct message for opcode 1
        self.mock_logger.log.assert_called_once_with(
            LogLevel.DEBUG, "write request from L1 data cache"
        )

    def test_logger_called_with_correct_message(self):
        """Test that the logger is called with the correct message for a specific opcode."""

        # Use an opcode with a known log message, e.g., 0 for "read request from L1 data cache"
        handle_event(0)

        # Check that the logger was called once with the expected message and log level
        self.mock_logger.log.assert_called_once_with(
            LogLevel.DEBUG, "read request from L1 data cache"
        )

    # Additional tests for other opcodes can be similarly added if needed.


if __name__ == "__main__":
    unittest.main()
