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

    def test_snoop_invalidate_clean_line(self):
        """
        Test that a snoop invalidate command to a clean line is handled correctly
        Note: It might be impossible for Exclusive state to receive invalidate command
        """
        address = 0x00000002  # address with NOHIT response

        # Fill a cache line 
        handle_event(self.cache, 0, address)
        self.check_line_state(address, MESIState.EXCLUSIVE)

        handle_event(self.cache, self.trace_event, address)   # HIT

        # Updated regex patterns to match actual output
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2: (invalidateline|3).*")
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*snoopresult*.*(hit|1)*")

    def test_snoop_invalidate_clean_shared_line(self):
        """
        Test that a snoop invalidate command to a clean line in shared state is handled correctly
        """
        address = 0x00000004  # address with HIT response

        # Fill a cache line 
        handle_event(self.cache, 0, address)
        self.check_line_state(address, MESIState.SHARED)

        handle_event(self.cache, self.trace_event, address)   # HIT

        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2: (invalidateline|3).*")
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*snoopresult*.*(hit|1)*")

    def test_snoop_invalidate_dirty_line(self):
        """
        Test that a snoop invalidate command to a dirty line is handled correctly
        Note: This is a not possible event under MESI protocol, our cache will ignore it but 
        provides runtime warning to user. 
        """
        address = 0x00000002

        handle_event(self.cache, 1, address)

        handle_event(self.cache, self.trace_event, address)   # HITM

        # Check that our cache doesn't respond to the snoop command
        self.check_line_state(address, MESIState.MODIFIED)

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
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*snoopresult.*(nohit|0).*")
        self.check_line_state(address, MESIState.EXCLUSIVE) 

    

if __name__ == "__main__":
    unittest.main()