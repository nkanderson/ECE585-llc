import unittest
from unittest.mock import MagicMock, patch
from cache.cache import Cache

from config.cache_config import CacheConfig
from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface
from common.constants import MESIState


class TestMESIProtocol(unittest.TestCase):
    """
    Test suite for MESI protocol implementation in the LLC.
    Focus on:
    1. State transitions based on processor operations
    2. Initial state determination based on snoop results
    3. Proper state management through cache operations
    """

    def setUp(self):
        """Create a fresh cache instance for each test"""
        cache_config = CacheConfig()
        # Mocking the config logger and args for testing
        self.mock_logger = MagicMock()
        self.mock_args = MagicMock(silent=False, debug=True)

        self.cache = Cache(cache_config, self.mock_logger)

        # Patch the config logger and args
        patch(
            "config.project_config.config.get_logger", return_value=self.mock_logger
        ).start()
        patch(
            "config.project_config.config.get_args", return_value=self.mock_args
        ).start()

        # TODO: Consider how to mock these instead
        BusInterface.initialize(self.mock_logger)
        L1Interface.initialize(self.mock_logger)

    def tearDown(self):
        # Stop any patches done during the test
        patch.stopall()

    def test_basic_mesi_state(self):
        """
        Basic processor side MESI state management test and lookup line method.
        TODO: AMore detailed test to come.

        Note:
            Address LSBs determine snoop results and thus initial state that the cache
            coherence protocol will set the line to:
            - 0b00: HIT -> SHARED
            - 0b01: HITM -> SHARED
            - 0b10/11: NOHIT -> EXCLUSIVE
        """
        # Test EXCLUSIVE state transition (using address ending in 0b10)
        addr_exclusive = 0x1234_5672  # Ends in 0b10

        # Initially line shouldn't be present
        line = self.cache.lookup_line(addr_exclusive)
        self.assertIsNone(line)

        # Read miss should result in EXCLUSIVE state since LSBs are 0b10 (NOHIT)
        self.cache.pr_read(addr_exclusive)
        line = self.cache.lookup_line(addr_exclusive)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.EXCLUSIVE)

        # Write to EXCLUSIVE line should change to MODIFIED
        self.cache.pr_write(addr_exclusive)
        line = self.cache.lookup_line(addr_exclusive)
        self.assertEqual(line.mesi_state, MESIState.MODIFIED)

        # Test SHARED state transition (using address ending in 0b00)
        addr_shared = 0x1234_5600  # Ends in 0b00

        # Read miss should result in SHARED state since LSBs are 0b00 (HIT)
        self.cache.pr_read(addr_shared)
        line = self.cache.lookup_line(addr_shared)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.SHARED)

        # Write to SHARED line should change to MODIFIED
        self.cache.pr_write(addr_shared)
        line = self.cache.lookup_line(addr_shared)
        self.assertEqual(line.mesi_state, MESIState.MODIFIED)

        # Test with HITM response (using address ending in 0b01)
        addr_hitm = 0x1234_5601  # Ends in 0b01

        # This is a read hit, and the line should be in MODIFIED state still
        # Nothing has happenend to change the state, so it should remain MODIFIED
        # GetSnoopResult returns HITM for this address, but that is a flaw in the
        # implementation Mark has given us because you shouldn't have a hit to a modified
        # line in another cache if we are the owners.
        self.cache.pr_read(addr_hitm)
        line = self.cache.lookup_line(addr_hitm)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.MODIFIED)

        # Verify non-existent line returns None
        non_existent_addr = 0x5555_5555
        line = self.cache.lookup_line(non_existent_addr)
        self.assertIsNone(line)

    # TODO: Add more detailed MESI tests:
    # - Test snoop handling
    # - Test victim line handling
    # - Test all possible state transitions
    # - Test multiple lines in same set with different states
    # - Test edge cases and error conditions


if __name__ == "__main__":
    unittest.main()
