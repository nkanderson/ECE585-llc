import unittest
from common.constants import MESIState, TraceCommand
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestPLRUPolicy(IntegrationSetup):

    def setUp(self):
        super().setUp()

        # Create an address to use in order to cause an eviction in a
        # full set populated with the self.single_set_addresses fixture
        # The addresses in single_set_addresses increment by 1 in the
        # 20th bit, so all ones in the MSBs will be a different tag
        self.new_tag_addr = (0xFFF << 20) | self.single_set_addresses[0]

    def test_sequential_access(self):
        """
        Test sequential access of each line in the set.
        This pattern shows true LRU eviction behavior.

        Requires the following sequence:
        - Read lines to fill all the ways of one cache set
        - Read one more
        - Confirm the first line in the set has been evicted
        """
        # Fill the cache set
        for addr in self.single_set_addresses:
            handle_event(self.cache, TraceCommand.L1_DATA_READ, addr)
            # Confirm the lines were allocated
            self.check_line_state(addr, MESIState.EXCLUSIVE)

        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.new_tag_addr)

        # Confirm new line and an existing line are still present, and the victim
        # is no longer valid
        self.check_line_state(self.new_tag_addr, MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[15], MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[0], MESIState.INVALID)

    def test_access_0_1_2(self):
        """
        Test sequential access of each line in the set,
        followed by access to ways 0, 1, and 2.
        This pattern shows pseudo LRU eviction behavior, where true LRU
        would evict way 4, this pattern will evict way 8.

        Requires the following sequence:
        - Read lines to fill all the ways of one cache set
        - Read ways 0, 1, and 2 again
        - Read one more
        - Confirm that way 8 has been evicted
        """
        # Fill the cache set
        for addr in self.single_set_addresses:
            handle_event(self.cache, TraceCommand.L1_DATA_READ, addr)
            # Confirm the lines were allocated
            self.check_line_state(addr, MESIState.EXCLUSIVE)

        # Access ways 0, 1, and 2
        handle_event(
            self.cache, TraceCommand.L1_DATA_READ, self.single_set_addresses[0]
        )
        handle_event(
            self.cache, TraceCommand.L1_DATA_READ, self.single_set_addresses[1]
        )
        handle_event(
            self.cache, TraceCommand.L1_DATA_READ, self.single_set_addresses[2]
        )

        # Read a new item in, causing an eviction
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.new_tag_addr)

        # Confirm new line and an existing line are still present, and the victim
        # is no longer valid
        self.check_line_state(self.new_tag_addr, MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[0], MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[8], MESIState.INVALID)

    def test_access_8_2(self):
        """
        Test sequential access of each line in the set,
        followed by access to ways 8 then 2.

        Requires the following sequence:
        - Read lines to fill all the ways of one cache set
        - Read ways 8 and 2 again
        - Read one more
        - Confirm the way 12 has been evicted
        """
        # Fill the cache set
        for addr in self.single_set_addresses:
            handle_event(self.cache, TraceCommand.L1_DATA_READ, addr)
            # Confirm the lines were allocated
            self.check_line_state(addr, MESIState.EXCLUSIVE)

        # Access way 8 then way 2
        handle_event(
            self.cache, TraceCommand.L1_DATA_READ, self.single_set_addresses[8]
        )
        handle_event(
            self.cache, TraceCommand.L1_DATA_READ, self.single_set_addresses[2]
        )

        # Read a new item in, causing an eviction
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.new_tag_addr)

        # Confirm new line and an existing line are still present, and the victim
        # is no longer valid
        self.check_line_state(self.new_tag_addr, MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[15], MESIState.EXCLUSIVE)
        self.check_line_state(self.single_set_addresses[12], MESIState.INVALID)


# Allow direct execution of this file
if __name__ == "__main__":
    unittest.main()
