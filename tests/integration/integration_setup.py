import unittest
from unittest.mock import MagicMock, patch
from cache.cache import Cache
from config.cache_config import CacheConfig
from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface


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

    # Placeholder for any teardown that needs to happen
    # after *each* test is run
    def tearDown(self):
        pass

    # Helper function to check MESI state
    def check_line_state(self, addr, expected_state):
        line = self.cache.lookup_line(addr)
        self.assertIsNotNone(line, f"Line at address {hex(addr)} not found in cache.")
        self.assertEqual(
            line.mesi_state,
            expected_state,
            f"Unexpected MESI state at address {hex(addr)}.",
        )
