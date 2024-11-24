import unittest
from unittest.mock import MagicMock, patch

from config.cache_config import CacheConfig
from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface
from cache.cache import Cache, AddressFields
from cache.cache_set import CacheLine
from common.constants import MESIState


class TestCache(unittest.TestCase):
    """Test basic functionality of cache, line lookup, and statistics tracking"""

    def setUp(self):
        """Create a cache instance with test configuration"""
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

    def test_cache_init(self):
        """Test cache initialization with default config from project_config.py"""
        self.assertEqual(self.cache.line_size, 64)  # 64 Bytes Cache Lines
        self.assertEqual(self.cache.associativity, 16)  # 16-way set associative
        self.assertEqual(self.cache.total_capacity, 16 * 2**20)  # 16 MB Cache
        self.assertEqual(self.cache.num_sets, 2**14)  # 16 MB/(assoc*64 B) = 2^14 sets
        self.assertEqual(self.cache.byte_select_bits, 6)  # (log2(64) = 6)
        self.assertEqual(self.cache.index_bits, 14)
        self.assertEqual(self.cache.tag_bits, 32 - 14 - 6)

    def test_decompose_address(self):
        """Test address decomposition into tag, index, and byte select fields"""
        # All zeros
        addr_fields = self.cache._Cache__decompose_address(0x0)
        self.assertEqual(addr_fields, AddressFields(tag=0, index=0, byte_select=0))
        # All ones
        addr_fields = self.cache._Cache__decompose_address(0xFFFF_FFFF)
        self.assertEqual(
            addr_fields,
            AddressFields(
                tag=0xFFF, index=0x3FFF, byte_select=0x3F  # Top 12 bits  # Next 14 bits
            ),
        )  # Bottom 6 bits

        addr = 0x1234_5678
        addr_fields = self.cache._Cache__decompose_address(addr)
        self.assertEqual(
            addr_fields,
            AddressFields(
                tag=addr >> (self.cache.index_bits + self.cache.byte_select_bits),
                index=(addr >> self.cache.byte_select_bits) & 0x3FFF,
                byte_select=addr & 0x3F,
            ),
        )

    def test_pr_read(self):
        """Test processor read operation and respective statistics tracking"""
        test_addresses = [0x1234_5678, 0x8765_4321, 0x1111_1111]
        accesses = 25
        expected_misses = 3
        expected_hits = 22

        # Generate 25 accesses to the cache, fill line after miss
        for i in range(accesses):
            hit = self.cache.pr_read(test_addresses[i % 3])
            if not hit:
                # Fill the line after miss
                self.cache.cache_line_fill(test_addresses[i % 3], MESIState.EXCLUSIVE)

        self.assertEqual(self.cache.statistics.cache_writes, 0)
        self.assertEqual(self.cache.statistics.cache_misses, expected_misses)
        self.assertEqual(self.cache.statistics.cache_hits, expected_hits)
        self.assertEqual(self.cache.statistics.cache_reads, accesses)

    def test_pr_write(self):
        """Test processor write operation with respective statistics tracking"""
        test_addresses = [0x1234_5678, 0x8765_4321, 0x1111_1111]
        accesses = 25
        expected_misses = 3
        expected_hits = 22

        # Generate 25 accesses to the cache, fill line after miss
        for i in range(accesses):
            hit = self.cache.pr_write(test_addresses[i % 3])
            if not hit:
                # Fill the line after miss
                self.cache.cache_line_fill(test_addresses[i % 3], MESIState.EXCLUSIVE)

        self.assertEqual(self.cache.statistics.cache_reads, 0)
        self.assertEqual(self.cache.statistics.cache_misses, expected_misses)
        self.assertEqual(self.cache.statistics.cache_hits, expected_hits)
        self.assertEqual(self.cache.statistics.cache_writes, accesses)

    def test_lookup_line(self):
        """Test line lookup functionality"""
        addr = 0x1234_5678

        # Initially line shouldn't be present
        self.assertIsNone(self.cache.lookup_line(addr))

        # Add line in Modified state
        self.cache.pr_write(addr)
        self.cache.cache_line_fill(addr, MESIState.MODIFIED)

        # Check lookup results
        line = self.cache.lookup_line(addr)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.MODIFIED)

    def test_cache_line_fill(self):
        """Test cache line fill operations"""
        addr = 0x1234_5678

        # Test initial fill
        self.assertIsNone(self.cache.lookup_line(addr))  # Verify line not present
        victim = self.cache.cache_line_fill(addr, MESIState.EXCLUSIVE)
        self.assertIsNone(victim)  # No victim on initial fill

        # Verify line was properly filled
        line = self.cache.lookup_line(addr)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.EXCLUSIVE)

        # Fill same line with a different state which is intended to throw a warning
        # State will not be modified and a warning will be printed
        victim = self.cache.cache_line_fill(addr, MESIState.MODIFIED)
        self.assertIsNone(victim)  # No victim when updating existing line
        line = self.cache.lookup_line(addr)
        self.assertEqual(line.mesi_state, MESIState.EXCLUSIVE)

        # Test replacement by filling entire set
        addr_fields = self.cache._Cache__decompose_address(addr)
        set_index = addr_fields.index

        # Fill rest of the set with different addresses but same index
        for i in range(1, self.cache.associativity):
            new_addr = addr + (
                i << (self.cache.index_bits + self.cache.byte_select_bits)
            )
            # Verify these addresses map to same set
            new_fields = self.cache._Cache__decompose_address(new_addr)
            self.assertEqual(new_fields.index, set_index)
            # Fill line
            victim = self.cache.cache_line_fill(new_addr, MESIState.EXCLUSIVE)
            self.assertIsNone(victim)  # Still shouldn't have victims

        # Now add one more line to force replacement
        replacement_addr = addr + (
            self.cache.associativity
            << (self.cache.index_bits + self.cache.byte_select_bits)
        )
        replacement_fields = self.cache._Cache__decompose_address(replacement_addr)
        self.assertEqual(replacement_fields.index, set_index)  # Verify same set

        # This should cause a replacement
        victim = self.cache.cache_line_fill(replacement_addr, MESIState.EXCLUSIVE)

        # Verify victim was returned
        self.assertIsNotNone(victim)
        self.assertIsInstance(victim, CacheLine)

        # Verify new line is present
        line = self.cache.lookup_line(replacement_addr)
        self.assertIsNotNone(line)
        self.assertEqual(line.mesi_state, MESIState.EXCLUSIVE)

    def test_clear_cache(self):
        """Test clearing the cache contents"""
        # Add some addresses to cache
        addresses = [0x1000, 0x2000, 0x3000, 0x4000, 0x5000]
        for addr in addresses:
            self.cache.pr_write(addr)
            self.cache.cache_line_fill(addr, MESIState.EXCLUSIVE)

        # Verify lines are present
        for addr in addresses:
            self.assertIsNotNone(self.cache.lookup_line(addr))

        # Clear the cache
        self.cache.clear_cache()

        # Verify all lines are gone
        for addr in addresses:
            self.assertIsNone(self.cache.lookup_line(addr))

    def test_print_cache(self):
        """Test printing cache contents"""
        import random

        # Initially cache should be empty
        print("\nPrinting empty cache:")
        self.cache.print_cache()

        # Generate 10 random addresses (ensuring they don't overlap)
        base_addr = 0x1000_0000
        random_addrs = [base_addr + (i * self.cache.line_size) for i in range(10)]

        # Add lines to cache with different MESI states
        states = [MESIState.MODIFIED, MESIState.EXCLUSIVE, MESIState.SHARED]

        for addr in random_addrs:
            self.cache.pr_write(addr)
            # Randomly choose a MESI state for each line
            state = random.choice(states)
            self.cache.cache_line_fill(addr, state)

        # Print cache with contents
        print(f"\nPrinting cache with {len(random_addrs)} lines:")
        self.cache.print_cache()
