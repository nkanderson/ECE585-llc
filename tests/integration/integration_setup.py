import re
import unittest
from unittest.mock import MagicMock, patch, call
from callee import Regex
from cache.cache import Cache
from config.cache_config import CacheConfig
from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface
from common.constants import LogLevel


class IntegrationSetup(unittest.TestCase):
    """
    Base setup for our integration tests.
    The tests and test fixtures assume our default cache configuration:
    - 32-bit addresses
    - 16 MiB cache capacity
    - 64 byte cache lines
    - MESI protocol
    - 16-way set associativity

    Extension of our integration test suite to support other configurations
    should entail creating different fixtures. Some of the individual tests
    may share logic (for example, in the event sequence), but will likely
    need modification to handle the specifics of other coherence protocols.
    """

    # Define class attributes with possible addresses for each snoop result
    # These will serve as fixtures for tests in child classes
    hit_addresses = [0x10000000, 0x20000004, 0x30000008, 0x4000000C]  # LSBs 00
    hitm_addresses = [0x10000001, 0x20000005, 0x30000009, 0x4000000D]  # LSBs 01
    nohit_addresses = [0x10000002, 0x20000006, 0x3000000A, 0x4000000F]  # LSBs 10 or 11

    # Setup resources for all tests in the class
    @classmethod
    def setUpClass(cls):
        # Initialize cache configuration and mocks
        cls.cache_config = CacheConfig()
        cls.mock_logger = MagicMock()
        cls.mock_args = MagicMock(silent=False, debug=True)

        # Patch the config logger and args
        patch(
            "config.project_config.config.get_logger", return_value=cls.mock_logger
        ).start()
        patch(
            "config.project_config.config.get_args", return_value=cls.mock_args
        ).start()

        # Need to ensure we're using new singleton instances
        # that have the current mock_logger
        BusInterface._bus_instance = None
        L1Interface._l1_instance = None
        BusInterface.initialize(cls.mock_logger)
        L1Interface.initialize(cls.mock_logger)

    # Cleanup after all tests in the class
    @classmethod
    def tearDownClass(cls):
        patch.stopall()

    def setUp(self):
        # Set up a new cache instance for each test using the
        # mocked logger that's shared across all tests
        self.cache = Cache(self.cache_config, self.mock_logger)

    # Teardown that needs to happen after *each* test is run
    def tearDown(self):
        self.mock_logger.reset_mock()

    # Helper function to check MESI state
    def check_line_state(self, addr, expected_state):
        line = self.cache.lookup_line(addr)
        self.assertIsNotNone(line, f"Line at address {hex(addr)} not found in cache.")
        self.assertEqual(
            line.mesi_state,
            expected_state,
            f"Unexpected MESI state at address {hex(addr)}.",
        )

    def assert_log_called_with_count(
        self, log_level: LogLevel, pattern: str, expected_count: int
    ):
        """
        Asserts that mock_logger.log is called a specified number of times with a specific log level
        and a message matching the regex pattern.

        Args:
            log_level: The expected log level (e.g., LogLevel.NORMAL).
            pattern: A raw string to use as a regex pattern to match in the log message.
            expected_count: The number of times the log call should occur with the specified log level
                            and message matching the pattern.

        Raises:
            AssertionError: If the log call with the specified arguments is not found the expected number of times.
        """
        # Extract 'log' calls only
        log_calls = [c for c in self.mock_logger.mock_calls if c[0] == "log"]

        # Define the expected call with regex for the second argument
        expected_call = call.log(log_level, Regex(pattern, flags=re.IGNORECASE))

        # Count occurrences of the expected call
        matching_calls = [c for c in log_calls if expected_call == c]

        # Assert the correct number of matching calls
        if len(matching_calls) != expected_count:
            raise AssertionError(
                f"Expected log call with level {log_level} and pattern '{pattern}' to be called exactly "
                f"{expected_count} times, but found {len(matching_calls)} matching calls."
            )

    def assert_log_called_once_with(self, log_level: LogLevel, pattern: str):
        """
        Asserts that mock_logger.log is called exactly once with a specific log level
        and a message matching the regex pattern.

        Args:
            log_level: The expected log level (e.g., LogLevel.NORMAL).
            pattern: A raw string to use as a regex pattern to match in the log message.

        Raises:
            AssertionError: If the log call with the specified arguments is not found exactly once.
        """
        self.assert_log_called_with_count(log_level, pattern, expected_count=1)
