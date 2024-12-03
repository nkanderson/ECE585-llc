import unittest
from common.constants import MESIState, LogLevel, TraceCommand
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestSnoopedReadRequest(IntegrationSetup):

    def setUp(self):
        super().setUp()
        self.trace_event = TraceCommand.SNOOP_READ
        # nohit_addr is an address that results in a simulated
        # NOHIT snoop response from other caches
        self.nohit_addr = self.nohit_addresses[0]
        # hit_addr is an address that results in a simulated
        # HIT snoop response from other caches
        self.hit_addr = self.hit_addresses[0]

    def test_exclusive(self):
        """
        Test snooping a read to a line in the Exclusive state.

        Requires the following sequence:
        - Read line (cache miss, NOHIT from other caches)
        - Snoop a read line (cache hit to E in our cache)
        """

        # Event 0: Read miss at self.nohit_addr (gets line in E state)
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 3: Snoop a read to the same address
        handle_event(self.cache, self.trace_event, self.nohit_addr)

        # Confirm our cache put the snoop result on the bus and updated state
        self.assert_log_called_once_with(LogLevel.NORMAL, r"snoopresult.*(hit|1)")
        self.check_line_state(self.nohit_addr, MESIState.SHARED)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_modified(self):
        """
        Test snooping a read to a line in the Modified state.

        Requires the following sequence:
        - Write line (cache miss, NOHIT from other caches)
        - Snoop a read line (cache hit to M in our cache)
        """
        # Event 1: Read miss at self.nohit_addr (gets line in M state)
        handle_event(self.cache, TraceCommand.L1_DATA_WRITE, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Event 3: Snoop a read to the same address
        handle_event(self.cache, self.trace_event, self.nohit_addr)

        # Confirm our cache put the snoop result on the bus and updated state
        self.assert_log_called_once_with(LogLevel.NORMAL, r"snoopresult.*(hitm|2)")
        self.check_line_state(self.nohit_addr, MESIState.SHARED)

        # Confirm our cache retrieved the line from L1 and wrote it back
        # We assume the reading cache can snarf it
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2: (getline|1).*")
        self.assert_log_called_once_with(
            LogLevel.NORMAL, r"busop.*(write|2).*address.*"
        )

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_shared(self):
        """
        Test snooping a read to a line in the Shared state.

        Requires the following sequence:
        - Read line (cache miss, HIT from other caches)
        - Snoop a read line (cache hit to S in our cache)
        """
        # Event 0: Read miss at self.hit_addr (gets line in S state)
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

        # Event 3: Snoop a read to the same address
        handle_event(self.cache, self.trace_event, self.nohit_addr)

        # Confirm our cache put the snoop result on the bus and stayed in S state
        self.assert_log_called_once_with(LogLevel.NORMAL, r"snoopresult.*(hit|1)")
        self.check_line_state(self.nohit_addr, MESIState.SHARED)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_invalid(self):
        """
        Test snooping a read to a line in the Invalid state.

        Requires the following sequence:
        - Snoop a read line (cache miss in our cache)
        """
        # Start with an invalid line
        self.check_line_state(self.hit_addr, MESIState.INVALID)

        # Event 3: Snoop a read to the same address
        handle_event(self.cache, self.trace_event, self.hit_addr)

        # Confirm our cache put the snoop result on the bus and stayed in I state
        self.assert_log_called_once_with(LogLevel.NORMAL, r"snoopresult.*(nohit|0)")
        self.check_line_state(self.nohit_addr, MESIState.INVALID)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 0)


# Allow direct execution of this file
if __name__ == "__main__":
    unittest.main()
