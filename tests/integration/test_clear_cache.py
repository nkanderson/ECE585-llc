import unittest
from common.constants import MESIState, LogLevel, TraceCommand
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestClearCache(IntegrationSetup):

    def setUp(self):
        super().setUp()
        self.trace_event = TraceCommand.CLEAR_CACHE

    def test_empty_cache(self):
        """
        Test clearing an empty cache.

        Should run without error and no output.
        """
        self.cache.clear_cache()

    def test_single_set(self):
        """
        Test clearing the cache with one occupied set.

        Requires the following sequence:
        - Read lines to fill all the ways of one cache set
        - Clear cache
        - Confirm those lines are not present
        """
        # Fill the cache set
        for addr in self.single_set_addresses:
            handle_event(self.cache, TraceCommand.L1_DATA_READ, addr)
            # Confirm the lines were allocated
            self.check_line_state(addr, MESIState.EXCLUSIVE)

        # Clear the cache
        self.cache.clear_cache()

        # Confirm lines are no longer valid in the cache
        for addr in self.single_set_addresses:
            self.check_line_state(addr, MESIState.INVALID)

    def test_all_sets(self):
        """
        Test clearing the cache with all sets occupied.

        Requires the following sequence:
        - Read lines to fill all cache sets with one address
        - Clear cache
        - Confirm those lines are not present
        """
        # Fill all cache sets
        for addr in self.all_sets_single_address:
            handle_event(self.cache, TraceCommand.L1_DATA_READ, addr)
            # Confirm the lines were allocated
            self.check_line_state(addr, MESIState.EXCLUSIVE)

        # Clear the cache
        self.cache.clear_cache()

        # Confirm lines are no longer valid in the cache
        for addr in self.all_sets_single_address:
            self.check_line_state(addr, MESIState.INVALID)


# Allow direct execution of this file
if __name__ == "__main__":
    unittest.main()
