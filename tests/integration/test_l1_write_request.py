import unittest
from common.constants import MESIState, LogLevel, TraceCommand
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestCommandL1WriteRequest(IntegrationSetup):

    def setUp(self):
        super().setUp()
        self.trace_event = TraceCommand.L1_DATA_WRITE
        # nohit_addr is an address that results in a simulated
        # NOHIT snoop response from other caches
        self.nohit_addr = self.nohit_addresses[0]
        # hit_addr is an address that results in a simulated
        # HIT snoop response from other caches
        self.hit_addr = self.hit_addresses[0]
        # hitm_addr is an address that results in a simulated
        # HITM snoop response from other caches
        self.hitm_addr = self.hitm_addresses[0]

    def test_exclusive(self):
        """
        Test writing a line in the Exclusive state.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Read line (cache miss)
        - Write same line (cache hit)
        """
        # Event 0: Read miss at self.nohit_addr (gets line in E state)
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.nohit_addr)

        # Confirm the L2 sendline message was issued for L1 request
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2.*sendline.*")

        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 1: Write hit at self.nohit_addr (should move to M state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # The second read event should not generate a bus operation, because
        # it was a hit to an exclusive line. So we'll test that there's only
        # been 1 of these bus operations issued in total.
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 1)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_modified(self):
        """
        Test writing a line in the Modified state.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Write line (cache miss)
        - Write same line (cache hit)
        """
        # Event 1: Write miss at self.nohit_addr (gets line in M state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)

        # Confirm the RWIM bus op was issued
        self.assert_log_called_once_with(LogLevel.NORMAL, r"busop.*(rwim|4).*")

        # Confirm the L2 sendline message was issued for L1 request
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2.*sendline.*")

        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Event 1: Write hit at self.nohit_addr (should stay in M state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 2)

        # TODO: Decide whether or not we want to assert additional busops
        # have *not* been issued, or if this one is even of value.
        self.assert_log_called_with_count(
            LogLevel.NORMAL, r"busop.*(write|2).*address.*", 0
        )

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 2)
        self.assertEqual(self.cache.statistics.cache_hits, 1)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_shared(self):
        """
        Test writing a line in the Shared state.
        Other caches return a HIT snoop response.

        Requires the following sequence:
        - Read line (cache miss)
        - Write line (cache hit)
        """
        # Event 0: Read miss at self.hit_addr (gets line in S state)
        handle_event(self.cache, TraceCommand.L1_DATA_READ, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

        # Event 1: Write hit at self.hit_addr (should move to M state)
        handle_event(self.cache, self.trace_event, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.MODIFIED)

        # Confirm the INVALIDATE bus op was issued
        self.assert_log_called_with_count(
            LogLevel.NORMAL, r"busop.*(invalidate|3).*", 1
        )

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 2)

        # Only the first read request should have resulted in a READ bus operation.
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*address")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 1)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_hitm(self):
        """
        Test writing a line that's been modified in another cache.
        Other caches return a HITM snoop response.

        Requires the following sequence:
        - Write line (cache miss, snarf from other cache flushWB)
        """
        # Event 1: Write miss at self.hitm_addr (gets line in M state)
        # Assumes cache with the modified line flushes the line
        # (with write-back) and our cache snarfs it
        handle_event(self.cache, self.trace_event, self.hitm_addr)
        self.check_line_state(self.hitm_addr, MESIState.MODIFIED)

        # Confirm the L2 sendline message was issued for L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 1)

        # Confirm the RWIM bus op was issued
        self.assert_log_called_once_with(LogLevel.NORMAL, r"busop.*(rwim|4).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_hit(self):
        """
        Test writing a line that's in a S or E state in another cache.
        Other cache(s) return a HIT snoop response.

        Requires the following sequence:
        - Write line (cache hit)
        """
        # Event 1: Write hit at self.hit_addr (should move to M state)
        handle_event(self.cache, self.trace_event, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.MODIFIED)

        # Confirm the L2 sendline message was issued for L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 1)

        # Confirm the RWIM bus op was issued
        self.assert_log_called_once_with(LogLevel.NORMAL, r"busop.*(rwim|4).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_clean_eviction(self):
        """
        Test writing a line that causes an eviction of a clean line.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Read lines to fill the cache (cache misses)
        - Write line to cause an eviction (cache miss)
        """
        # Base addr that returns a NOHIT snoop response from other caches
        address = 0x00000002  # Start with set 0, offset with NOHIT response
        increment = 0x100000  # 1 MiB increment to change the tag

        # Fill the cache
        for _i in range(16):
            address += increment
            handle_event(self.cache, TraceCommand.L1_DATA_READ, address)
            self.check_line_state(address, MESIState.EXCLUSIVE)

        # One write to trigger an eviction of a clean line
        handle_event(self.cache, self.trace_event, address + increment)

        # Confirm the L2 sendline message was issued for each L1 request (reads and write)
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 17)

        # Check for one READ bus operation per cache miss
        self.assert_log_called_with_count(
            LogLevel.NORMAL, r".*busop.*(read|1).*address", 16
        )

        # Confirm the L2 message to L1 for evictline was issued
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*evictline.*", 1)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 16)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 17)

    def test_dirty_eviction(self):
        """
        Test writing a line that causes an eviction of a dirty line.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Write lines to fill the cache (cache misses)
        - Write line to cause an eviction (cache miss)
        """
        # Base addr that returns a NOHIT snoop response from other caches
        address = 0x00000002  # Start with set 0, offset with NOHIT response
        increment = 0x100000  # 1 MiB increment to change the tag

        # Fill the cache
        for _i in range(16):
            address += increment
            handle_event(self.cache, 1, address)
            self.check_line_state(address, MESIState.MODIFIED)

        # One write to trigger an eviction of a clean line
        handle_event(self.cache, self.trace_event, address + increment)

        # Confirm the L2 sendline message was issued for each L1 request (reads and write)
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 17)

        # Check for one READ bus operation per cache miss
        self.assert_log_called_with_count(
            LogLevel.NORMAL, r".*busop.*(rwim|4).*address", 17
        )

        # Confirm the L2 messages to L1 for eviction were issued
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*getline.*", 1)
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*evictline.*", 1)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_writes, 17)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 17)


# Allow direct execution of this file
if __name__ == "__main__":
    unittest.main()
