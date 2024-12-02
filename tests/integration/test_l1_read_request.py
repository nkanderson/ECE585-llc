import re
import unittest
from callee import Regex
from common.constants import MESIState, LogLevel
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestCommandL1ReadRequestData(IntegrationSetup):

    def setUp(self):
        super().setUp()
        # Default to 0 for trace event op code.
        # This allows us to create a child class for the instruction read requests,
        # which should have identical behavior.
        self.trace_event = 0
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
        Test reading a line in the Exclusive state.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Read line (cache miss)
        - Read line (cache hit)
        """
        # Increment expected stats values based on actions we expect to
        # modify the cache statistics object
        # Note: these values are not determined by the actual return value
        # of the functions being called
        expected_reads = 0
        expected_writes = 0
        expected_hits = 0
        expected_misses = 0

        # Event 0: Read miss at self.nohit_addr (gets line in E state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)

        # Confirm the L2 sendline message was issued
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2.*sendline.*")

        # Check that a bus operation was issued, once per read event
        # with either the name (read) or the operation ID number
        self.mock_logger.log.assert_any_call(
            LogLevel.NORMAL,
            Regex(r".*busop.*(read|1).*", flags=re.IGNORECASE),
        )

        expected_misses += 1
        expected_reads += 1
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 0: Read hit at self.nohit_addr (should stay in E state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)
        expected_hits += 1
        expected_reads += 1
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # The second read event should not generate a bus operation, because
        # it was a hit to an exclusive line. So we'll test that there's only
        # been 1 of these bus operations issued in total.
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, expected_reads)
        self.assertEqual(self.cache.statistics.cache_writes, expected_writes)
        self.assertEqual(self.cache.statistics.cache_hits, expected_hits)
        self.assertEqual(self.cache.statistics.cache_misses, expected_misses)

    def test_modified(self):
        """
        Test reading a line in the Modified state.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Read line (cache miss)
        - Write line (cache hit)
        - Read line (cache hit)
        """
        # Event 0: Read miss at self.nohit_addr (gets line in E state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 1: Write hit at self.nohit_addr (line moves to M state)
        handle_event(self.cache, 1, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Event 0: Read hit at self.nohit_addr (should stay in M state)
        handle_event(self.cache, self.trace_event, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 3)

        # Only the first read request should have resulted in a READ
        # bus operation.
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*")

        # Assertions for statistics
        # As an alternative to the above that accumulates the expected
        # stats values, we can hardcode them here, which may be more
        # readable.
        self.assertEqual(self.cache.statistics.cache_reads, 2)
        self.assertEqual(self.cache.statistics.cache_writes, 1)
        self.assertEqual(self.cache.statistics.cache_hits, 2)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_shared(self):
        """
        Test reading a line in the Shared state.
        Other caches return a HIT snoop response.

        Requires the following sequence:
        - Read line (cache miss)
        - Read line (cache hit)
        """
        # Event 0: Read miss at self.hit_addr (gets line in S state)
        handle_event(self.cache, self.trace_event, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

        # Event 0: Read hit at self.hit_addr (should stay in S state)
        handle_event(self.cache, self.trace_event, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 2)

        # Only the first read request should have resulted in a READ
        # bus operation.
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 2)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 1)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_hitm(self):
        """
        Test reading a line that's been modified in another cache.
        Other caches return a HITM snoop response.

        Requires the following sequence:
        - Read line (cache miss, snarf from other cache flushWB)
        """
        # Event 0: Read miss at self.hitm_addr (gets line in S state)
        # Assumes cache with the modified line flushes the line
        # (with write-back) and our cache snarfs it
        handle_event(self.cache, self.trace_event, self.hitm_addr)
        self.check_line_state(self.hitm_addr, MESIState.SHARED)

        # Confirm the L2 sendline message was issued
        self.assert_log_called_once_with(LogLevel.NORMAL, r"l2.*sendline.*")

        # Check for a single READ bus operation
        self.assert_log_called_once_with(LogLevel.NORMAL, r".*busop.*(read|1).*")

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 1)

    def test_clean_eviction(self):
        """
        Test reading a line that causes an eviction of a clean line.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Read lines to fill the cache (cache misses)
        - Read line to cause an eviction (cache miss)
        """
        # Base addr that returns a NOHIT snoop response from other caches
        address = 0x00000002  # Start with set 0, offset with NOHIT response
        increment = 0x100000  # 1 MiB increment to change the tag

        # Fill the cache
        for _i in range(16):
            address += increment
            handle_event(self.cache, self.trace_event, address)
            self.check_line_state(address, MESIState.EXCLUSIVE)

        # One more read to trigger an eviction of a clean line
        handle_event(self.cache, self.trace_event, address + increment)

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 17)

        # Check for one READ bus operation per cache miss
        self.assert_log_called_with_count(LogLevel.NORMAL, r".*busop.*(read|1).*", 17)

        # Confirm the L2 message to L1 for evictline was issued
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*evictline.*", 1)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 17)
        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 17)

    def test_dirty_eviction(self):
        """
        Test reading a line that causes an eviction of a dirty line.
        Other caches return a NOHIT snoop response.

        Requires the following sequence:
        - Write lines to fill the cache (cache misses)
        - Read line to cause an eviction (cache miss)
        """
        # Base addr that returns a NOHIT snoop response from other caches
        address = 0x00000002  # Start with set 0, offset with NOHIT response
        increment = 0x100000  # 1 MiB increment to change the tag

        # Fill the cache
        for _i in range(16):
            address += increment
            handle_event(self.cache, 1, address)
            self.check_line_state(address, MESIState.MODIFIED)

        # One more read to trigger an eviction of a dirty line
        handle_event(self.cache, self.trace_event, address + increment)

        # Confirm the L2 sendline message was issued for each L1 request
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*sendline.*", 17)

        # Check for one RWIM bus operation per cache miss
        self.assert_log_called_with_count(LogLevel.NORMAL, r".*busop.*(rwim|4).*", 16)

        # Confirm bus op for read request was issued
        self.assert_log_called_with_count(
            LogLevel.NORMAL, r".*busop.*(read|1).*address", 1
        )

        # Confirm the L2 messages to L1 for eviction were issued
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*getline.*", 1)
        self.assert_log_called_with_count(LogLevel.NORMAL, r"l2.*evictline.*", 1)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 16)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 17)


# In order to test events 0 and 2, we need to create a child class for
# one of the events only. The tests from the parent class are loaded
# automatically.
# Unittest does not seem to have a very clean way of parameterizing
# a set of tests such as those above. If we find ourselves replicating
# the pattern in this file for parameterization, it may be time to look
# into switching to pytest.
class TestCommandL1ReadRequestInstruction(TestCommandL1ReadRequestData):
    """
    Run all of the above tests for trace event op code 2.
    Since the LLC is unified, the L1 read requests for data
    and instructions should have the same behavior.
    """

    def setUp(self):
        super().setUp()
        self.trace_event = 2


# Allow direct execution of this file
if __name__ == "__main__":
    unittest.main()
