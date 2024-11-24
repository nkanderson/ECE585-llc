import unittest
from unittest.mock import MagicMock, patch
from cache.cache import Cache

from config.cache_config import CacheConfig

from utils.event_handler import handle_event


class TestEventHandler(unittest.TestCase):
    """
    Tests that the appropriate cache methods are called for each event opcode.
    """

    def setUp(self):
        cache_config = CacheConfig()

        # Mocking the config logger and args for testing
        self.mock_logger = MagicMock()
        self.mock_args = MagicMock(silent=False, debug=True)

        self.cache = Cache(cache_config, self.mock_logger)

        # Replace cache methods with MagicMocks
        self.cache.pr_read = MagicMock()
        self.cache.pr_write = MagicMock()
        self.cache.handle_snoop = MagicMock()
        self.cache.clear_cache = MagicMock()
        self.cache.print_cache = MagicMock()

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

    def test_handle_event_with_pr_read(self):
        """Test that handle_event appropriately calls cache.pr_read()."""

        # Test for op codes 0 and 2, read request from L1
        for opcode in [0, 2]:
            with self.subTest(opcode=opcode):
                # Reset mock so that calls do not accumulate between
                # different opcode tests
                self.cache.pr_read.reset_mock()
                handle_event(self.cache, opcode, addr=0x1234)

                # Assert pr_read was called with the correct address
                self.cache.pr_read.assert_called_once_with(0x1234)

                # Ensure other methods are not called
                self.cache.pr_write.assert_not_called()
                self.cache.handle_snoop.assert_not_called()
                self.cache.clear_cache.assert_not_called()
                self.cache.print_cache.assert_not_called()

    def test_handle_event_with_pr_write(self):
        """Test that handle_event appropriately calls cache.pr_write()."""
        opcode = 1
        handle_event(self.cache, opcode, addr=0x5678)

        # Assert pr_write was called with the correct address
        self.cache.pr_write.assert_called_once_with(0x5678)

        # Ensure other methods are not called
        self.cache.pr_read.assert_not_called()
        self.cache.handle_snoop.assert_not_called()
        self.cache.clear_cache.assert_not_called()
        self.cache.print_cache.assert_not_called()

    def test_handle_event_with_handle_snoop(self):
        """Test that handle_event appropriately calls cache.handle_snoop()."""
        for opcode in [3, 4, 5, 6]:
            with self.subTest(opcode=opcode):
                # Reset mock so that calls do not accumulate between
                # different opcode tests
                self.cache.handle_snoop.reset_mock()
                handle_event(self.cache, opcode, addr=0x9ABC)

                # Assert handle_snoop was called with the correct address
                self.cache.handle_snoop.assert_called_once_with(opcode, 0x9ABC)

                # Ensure other methods are not called
                self.cache.pr_read.assert_not_called()
                self.cache.pr_write.assert_not_called()
                self.cache.clear_cache.assert_not_called()
                self.cache.print_cache.assert_not_called()

    def test_handle_event_with_clear_cache(self):
        opcode = 8
        handle_event(self.cache, opcode)

        # Assert clear_cache was called
        self.cache.clear_cache.assert_called_once()

        # Ensure other methods are not called
        self.cache.pr_read.assert_not_called()
        self.cache.pr_write.assert_not_called()
        self.cache.handle_snoop.assert_not_called()
        self.cache.print_cache.assert_not_called()

    def test_handle_event_with_print_cache(self):
        event_opcode = 9
        handle_event(self.cache, event_opcode)

        # Assert print_cache was called
        self.cache.print_cache.assert_called_once()

        # Ensure other methods are not called
        self.cache.pr_read.assert_not_called()
        self.cache.pr_write.assert_not_called()
        self.cache.handle_snoop.assert_not_called()
        self.cache.clear_cache.assert_not_called()


if __name__ == "__main__":
    unittest.main()
