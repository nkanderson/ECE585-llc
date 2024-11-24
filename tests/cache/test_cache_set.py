import unittest

from cache.cache_set import CacheSetPLRUMESI
from common.constants import MESIState

class TestCacheSet(unittest.TestCase):
    """Unit tests for CacheSet implementation"""

    def setUp(self):
        """Create a default 16-way cache set for testing"""
        self.cache_set = CacheSetPLRUMESI(num_ways=16)

    def test_constructor_validation(self):
        """Test constructor parameter validation"""
        # Valid cases
        valid_ways = [1, 2, 4, 8, 16, 32]
        for ways in valid_ways:
            with self.subTest(ways=ways):
                cache_set = CacheSetPLRUMESI(num_ways=ways)
                # Confirms number of n-ways set associativity
                self.assertEqual(cache_set.associativity, ways)

        # Invalid cases, confirms proper exceptions are raised
        with self.assertRaises(TypeError):
            CacheSetPLRUMESI(num_ways=2.5)
        with self.assertRaises(TypeError):
            CacheSetPLRUMESI(num_ways="16")
        with self.assertRaises(ValueError):
            CacheSetPLRUMESI(num_ways=0)
        with self.assertRaises(ValueError):
            CacheSetPLRUMESI(num_ways=33)
        with self.assertRaises(ValueError):
            CacheSetPLRUMESI(num_ways=-1)
        with self.assertRaises(ValueError):
            CacheSetPLRUMESI(num_ways=3)  # Not power of 2

    def test_initial_state(self):
        """Test initial state of newly created cache set"""
        self.assertEqual(len(self.cache_set.ways), 16)
        self.assertEqual(self.cache_set.state, 0)  # Initial PLRU state

        # Check all ways are properly initialized
        for way in self.cache_set.ways:
            self.assertEqual(way.tag, 0)
            self.assertTrue(way.is_invalid())

    def test_search_and_allocate(self):
        """Test cache search and allocation operations with PLRU updates"""
        # Test search on empty cache - should miss
        self.assertIsNone(self.cache_set.search_set(0x1234))

        # Allocate a line and verify search hit
        self.cache_set.allocate(0x1234, MESIState.EXCLUSIVE)
        # Test processor side request (updates PLRU)
        way_index = self.cache_set.search_set(0x1234, update_plru=True)
        self.assertIsNotNone(way_index)
        self.assertEqual(self.cache_set.mesi_state[way_index], MESIState.EXCLUSIVE)

        # Test snoop request (no PLRU update)
        way_index = self.cache_set.search_set(0x1234, update_plru=False)
        self.assertIsNotNone(way_index)

        # Search miss on different tag
        self.assertIsNone(self.cache_set.search_set(0x5678))

    def test_allocation_with_mesi(self):
        """Test cache line allocation with different MESI states"""
        # Allocate first line as EXCLUSIVE
        victim_line, way = self.cache_set.allocate(0x1234, MESIState.EXCLUSIVE)
        self.assertIsNone(victim_line)  # No victim on first allocation
        self.assertEqual(self.cache_set.mesi_state[way], MESIState.EXCLUSIVE)

        # Allocate second line as SHARED
        victim_line, way = self.cache_set.allocate(0x5678, MESIState.SHARED)
        self.assertIsNone(victim_line)
        self.assertEqual(self.cache_set.mesi_state[way], MESIState.SHARED)

        # Fill rest of set to force eviction
        for i in range(2, self.cache_set.num_ways):
            self.cache_set.allocate(0x1000 + i, MESIState.EXCLUSIVE)

        # Next allocation should cause eviction
        victim_line, way = self.cache_set.allocate(0xAAAA, MESIState.MODIFIED)
        self.assertIsNotNone(victim_line)
        self.assertEqual(self.cache_set.mesi_state[way], MESIState.MODIFIED)

    def test_plru_update(self):
        """Test PLRU bit updates after access (basic test)
        When accessing a way:
            - Left child access: set parent bit to 0
            - Right child access: set parent bit to 1
        """
        # Access first way
        self.cache_set._CacheSetPLRUMESI__update_plru(0)
        expected_state = 0b000_0000_0000_0000
        print("After way 0 access:")
        print(f"Current state:  {self.cache_set.state:015b}")
        print(f"Expected state: {expected_state:015b}")
        self.assertEqual(self.cache_set.state, expected_state)

        # Access second way
        self.cache_set._CacheSetPLRUMESI__update_plru(1)
        expected_state = 0b000_0000_1000_0000
        print("After way 1 access:")
        print(f"Current state:  {self.cache_set.state:015b}")
        print(f"Expected state: {expected_state:015b}")
        self.assertEqual(self.cache_set.state, expected_state)

        # Test way 8 access
        self.cache_set._CacheSetPLRUMESI__update_plru(8)
        expected_state = 0b000_0000_1000_0001
        print("After way 8 access:")
        print(f"Current state:  {self.cache_set.state:015b}")
        print(f"Expected state: {expected_state:015b}")
        self.assertEqual(self.cache_set.state, expected_state)

        # Test way 15 access
        self.cache_set._CacheSetPLRUMESI__update_plru(15)
        expected_state = 0b100_0000_1100_0101
        print("After way 15 access: ")
        print(f"Current state:  {self.cache_set.state:015b}")
        print(f"Expected state: {expected_state:015b}")
        self.assertEqual(self.cache_set.state, expected_state)

    def test_plru_behavior(self):
        """
        Test of PLRU behavior using predefined test cases that
        model real cache access patterns. Each test case verifies both the
        PLRU state updates and victim selection.
        """
        test_cases = [
            {
                "name": "Sequential Access to All 16 Ways, then access 8, and 2 repectively",
                "access_pattern": [
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    8,
                    2,
                ],
                "states": [
                    (0, 0b000_0000_0000_0000),  # After way 0
                    (1, 0b000_0000_1000_0000),  # After way 1
                    (2, 0b000_0000_1000_1000),  # After way 2
                    (3, 0b000_0001_1000_1000),  # After way 3
                    (4, 0b000_0001_1000_1010),  # After way 4
                    (5, 0b000_0011_1000_1010),  # After way 5
                    (6, 0b000_0011_1001_1010),  # After way 6
                    (7, 0b000_0111_1001_1010),  # After way 7
                    (8, 0b000_0111_1001_1011),  # After way 8
                    (9, 0b000_1111_1001_1011),  # After way 9
                    (10, 0b000_1111_1011_1011),  # After way 10
                    (11, 0b001_1111_1011_1011),  # After way 11
                    (12, 0b001_1111_1011_1111),  # After way 12
                    (13, 0b011_1111_1011_1111),  # After way 13
                    (14, 0b011_1111_1111_1111),  # After way 14
                    (15, 0b111_1111_1111_1111),  # After way 15 (last way, set now full)
                    (8, 0b111_0111_1101_1011),  # After way 8
                    (2, 0b111_0110_1101_1000),  # After way 2
                ],
                "expected_victim": 12,
            },
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case["name"]):
                # Reset cache state for each test case
                self.setUp()

                # Execute access pattern and verify states
                for i, way in enumerate(test_case["access_pattern"]):
                    self.cache_set._CacheSetPLRUMESI__update_plru(way)
                    expected_way, expected_state = test_case["states"][i]

                    # Debug output
                    print(f"\n{test_case['name']} - After way {way} access:")
                    print(f"Current state:  {self.cache_set.state:015b}")
                    print(f"Expected state: {expected_state:015b}")

                    self.assertEqual(
                        self.cache_set.state,
                        expected_state,
                        f"PLRU state mismatch after accessing way {way}",
                    )

                # Verify final victim selection
                victim = self.cache_set._CacheSetPLRUMESI__get_plru_victim()
                self.assertEqual(
                    victim,
                    test_case["expected_victim"],
                    f"Wrong victim selected. Expected {test_case['expected_victim']}, got {victim}",
                )

    def test_plru_allocation_sequence(self):
        """
        Test PLRU behavior during a realistic allocation sequence.
        First fill all ways sequentially, then access ways 8 and 2,
        and finally allocate a new line which should evict way 12.
        
        This test verifies:
        1. Initial allocation sequence uses ways in order
        2. PLRU bits are properly updated during allocations
        3. PLRU bits are properly updated during searches
        4. Victim selection follows PLRU policy
        """
        # Fill all ways sequentially
        allocation_sequence = [
            {"tag": i, "expected_way": i} for i in range(16)
        ]

        # Perform initial allocations
        for i, alloc in enumerate(allocation_sequence):
            with self.subTest(step=f"Initial allocation {i}"):
                # Allocate new line with EXCLUSIVE state
                victim_line, way = self.cache_set.allocate(
                    alloc["tag"], 
                    state=MESIState.EXCLUSIVE
                )
                
                # Debug output
                print(f"\nAllocation {i} - Tag {hex(alloc['tag'])}:")
                print(f"Selected way: {way}")
                print(f"PLRU state:  {self.cache_set.state:015b}")
                
                # Verify allocation
                self.assertEqual(way, alloc["expected_way"])
                self.assertIsNone(victim_line)  # No victims during initial fill

        # Access way 8 and 2 using search_set with PLRU update
        way8 = self.cache_set.search_set(0x8, update_plru=True)
        self.assertIsNotNone(way8)
        self.assertEqual(way8, 8)

        way2 = self.cache_set.search_set(0x2, update_plru=True)
        self.assertIsNotNone(way2)
        self.assertEqual(way2, 2)

        # Now allocate a new line - should evict way 12
        victim_line, way = self.cache_set.allocate(0xAAAA, state=MESIState.EXCLUSIVE)
        
        # Debug output
        print("\nFinal allocation - Tag 0xAAAA:")
        print(f"Selected way: {way}")
        print(f"PLRU state:  {self.cache_set.state:015b}")  # Expected: 0b101_0110_1001_1101
        print(f"Victim tag:  {hex(victim_line.tag) if victim_line else None}")

        # Verify final allocation
        self.assertEqual(way, 12, "PLRU should select way 12 for replacement")
        self.assertIsNotNone(victim_line, "Should have evicted a line")
        self.assertEqual(
            victim_line.tag, 
            0xC, 
            f"Wrong line evicted, expected 0xC got {hex(victim_line.tag)}"
        )
        self.assertEqual(
            victim_line.mesi_state, 
            MESIState.EXCLUSIVE, 
            "Evicted line should have been in EXCLUSIVE state"
        )

    def test_print_set(self):
        """Test printing of valid lines in the set"""
        # Create a fresh cache set instance specifically for this test
        cache_set = CacheSetPLRUMESI(num_ways=16)

        print("\nTesting empty set, should be no output:")
        cache_set.print_set()  # Should print nothing for empty set

        print("\nTesting set with valid lines:")
        cache_set.allocate(0x1234, MESIState.MODIFIED)
        cache_set.allocate(0x5678, MESIState.SHARED)
        cache_set.allocate(0x9ABC, MESIState.EXCLUSIVE)
        cache_set.allocate(0xDEF0, MESIState.INVALID)
        cache_set.print_set()  # Should print the valid lines


    def test_mesi_state_descriptor(self): 
            # Create a fresh cache set
        cache_set = CacheSetPLRUMESI(num_ways=4)
        
        # Allocate a line in EXCLUSIVE state
        cache_set.allocate(0x1234, state=MESIState.EXCLUSIVE)
        
        # Test getting state
        self.assertEqual(cache_set.mesi_state[0], MESIState.EXCLUSIVE)
        
        # Test setting state
        cache_set.mesi_state[0] = MESIState.MODIFIED  # EXCLUSIVE -> MODIFIED ok
        self.assertEqual(cache_set.mesi_state[0], MESIState.MODIFIED)
        
        # Test invalid way index
        with self.assertRaises(IndexError):
            _ = cache_set.mesi_state[4]  # Way 4 doesn't exist in 4-way cache

if __name__ == "__main__":
    unittest.main(verbosity=2)
