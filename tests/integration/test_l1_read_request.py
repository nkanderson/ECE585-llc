import unittest
from common.constants import MESIState
from utils.event_handler import handle_event
from tests.integration.integration_setup import IntegrationSetup


class TestCommandL1ReadRequestData(IntegrationSetup):

    def setUp(self):
        super().setUp()
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
        # Increment expected stats values based on actions we
        # expect to modify the cache statistics object
        # Note: these values are not determined by the actual
        # return value of the functions being called
        expected_reads = 0
        expected_writes = 0
        expected_hits = 0
        expected_misses = 0

        # Event 0: Read miss at self.nohit_addr (gets line in E state)
        handle_event(self.cache, 0, self.nohit_addr)
        expected_misses += 1
        expected_reads += 1
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 0: Read hit at self.nohit_addr (should stay in E state)
        handle_event(self.cache, 0, self.nohit_addr)
        expected_hits += 1
        expected_reads += 1
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

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
        handle_event(self.cache, 0, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.EXCLUSIVE)

        # Event 1: Write hit at self.nohit_addr (line moves to M state)
        handle_event(self.cache, 1, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

        # Event 0: Read hit at self.nohit_addr (should stay in M state)
        handle_event(self.cache, 0, self.nohit_addr)
        self.check_line_state(self.nohit_addr, MESIState.MODIFIED)

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
        handle_event(self.cache, 0, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

        # Event 0: Read hit at self.hit_addr (should stay in S state)
        handle_event(self.cache, 0, self.hit_addr)
        self.check_line_state(self.hit_addr, MESIState.SHARED)

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
        handle_event(self.cache, 0, self.hitm_addr)
        self.check_line_state(self.hitm_addr, MESIState.SHARED)

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
            handle_event(self.cache, 0, address)
            self.check_line_state(address, MESIState.EXCLUSIVE)

        # One more read to trigger an eviction of a clean line
        handle_event(self.cache, 0, address + increment)

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
        handle_event(self.cache, 0, address + increment)

        # Assertions for statistics
        self.assertEqual(self.cache.statistics.cache_reads, 1)
        self.assertEqual(self.cache.statistics.cache_writes, 16)
        self.assertEqual(self.cache.statistics.cache_hits, 0)
        self.assertEqual(self.cache.statistics.cache_misses, 17)


if __name__ == "__main__":
    unittest.main()
