import re
import unittest
from callee import Regex
from common.constants import MESIState, LogLevel
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup

class TestCommandSnoopedInvalidate(IntegrationSetup):
    
    def setUp(self):
        super().setUp()
        
        self.trace_event = 6

    def assert_line_invalid(self, address):
        """
        Assert that the line in the cache is invalid
        """
        line = self.cache.lookup_line(address)

        if line is not None: 
            raise AssertionError(f"Line at address {address:08x} is not invalid")


    def test_snoop_invalidate_clean_line(self):
        """
        Test that a snoop invalidate command to a clean line is handled correctly
        """
        address = 0x00000002  # Start with set 0, offset with NOHIT response

        # Fill a cache line 
        handle_event(self.cache, 0, address)

        handle_event(self.cache, self.trace_event, address)   # HIT

        # Updated regex patterns to match actual output
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i)L2.*INVALIDATELINE.*")
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i).*Snoop Result: HIT.*")

    def test_snoop_invalidate_dirty_line(self):
        """
        Test that a snoop invalidate command to a dirty line is handled correctly
        """
        address = 0x00000002

        handle_event(self.cache, 1, address)

        handle_event(self.cache, self.trace_event, address)   # HITM

        # Checks the our cache puts the snoop result
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i).*Snoop Result: HITM.*")
        # Chcek that we are getting most recent data from L1
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i)L2.*GETLINE.*")
        # Check that we then invalidate line in L1
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i)L2.*INVALIDATELINE.*")
        # Check that we are performing a writeback
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i)BusOp.*WRITE.*")
        # Check that our cache no longer has the data
        self.assert_line_invalid(address)

    def test_snoop_invalidate_invalid_line(self):
        """
        Test that a snoop invalidate command to an invalid line is handled correctly
        """
        address = 0x00000002
        increment = 0x100000  # Increment tag

        handle_event(self.cache, 0, address)

        # Check that we are not doing anything
        handle_event(self.cache, self.trace_event, address + increment) # MISS

        # Check that we are not doing anything except putting the snoop result
        self.assert_log_called_once_with(LogLevel.NORMAL, r"(?i)^Address: [0-9a-f]{8}, Snoop Result: NOHIT$")
        self.check_line_state(address, MESIState.EXCLUSIVE) 

if __name__ == "__main__":
    unittest.main()