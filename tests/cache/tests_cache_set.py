import unittest

from cache.cache_set import CacheSetPLRUMESI


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
                self.assertEqual(cache_set.associativity, ways)

        # Invalid cases
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
            self.assertIsNone(way.tag)
            self.assertTrue(way.is_invalid())

    def test_read_operations(self):
        """Test cache read operations"""
        # Read miss on empty cache
        self.assertFalse(self.cache_set.read(0x1234))

        # Allocate line and verify read hit
        self.cache_set.allocate(0x1234)
        self.assertTrue(self.cache_set.read(0x1234))

        # Read miss on different tag
        self.assertFalse(self.cache_set.read(0x5678))

    def test_write_operations(self):
        """Test cache write operations"""
        # Write miss on empty cache
        self.assertFalse(self.cache_set.write(0x1234))

        # Allocate line and verify write hit
        self.cache_set.allocate(0x1234)
        self.assertTrue(self.cache_set.write(0x1234))

        # Write miss on different tag
        self.assertFalse(self.cache_set.write(0x5678))

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
                    (15, 0b111_1111_1111_1111),  # After way 15
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
        """
        # Fill all ways sequentially
        allocation_sequence = [
            {"tag": 0x0, "expected_way": 0, "expected_victim": None},
            {"tag": 0x1, "expected_way": 1, "expected_victim": None},
            {"tag": 0x2, "expected_way": 2, "expected_victim": None},
            {"tag": 0x3, "expected_way": 3, "expected_victim": None},
            {"tag": 0x4, "expected_way": 4, "expected_victim": None},
            {"tag": 0x5, "expected_way": 5, "expected_victim": None},
            {"tag": 0x6, "expected_way": 6, "expected_victim": None},
            {"tag": 0x7, "expected_way": 7, "expected_victim": None},
            {"tag": 0x8, "expected_way": 8, "expected_victim": None},
            {"tag": 0x9, "expected_way": 9, "expected_victim": None},
            {"tag": 0xA, "expected_way": 10, "expected_victim": None},
            {"tag": 0xB, "expected_way": 11, "expected_victim": None},
            {"tag": 0xC, "expected_way": 12, "expected_victim": None},
            {"tag": 0xD, "expected_way": 13, "expected_victim": None},
            {"tag": 0xE, "expected_way": 14, "expected_victim": None},
            {"tag": 0xF, "expected_way": 15, "expected_victim": None},
        ]

        # Perform initial allocations
        for i, alloc in enumerate(allocation_sequence):
            with self.subTest(step=f"Initial allocation {i}"):
                victim_line, way = self.cache_set.allocate(alloc["tag"])
                print(f"\nAllocation {i} - Tag {hex(alloc['tag'])}:")
                print(f"Selected way: {way}")
                print(f"PLRU state:   {self.cache_set.state:015b}")

                self.assertEqual(way, alloc["expected_way"])
                self.assertIsNone(victim_line)  # No victims during initial fill

        # Access way 8 and 2 to match the PLRU pattern
        self.assertTrue(self.cache_set.read(0x8))  # Access way 8
        self.assertTrue(self.cache_set.read(0x2))  # Access way 2

        # Now allocate a new line - should evict way 12
        victim_line, way = self.cache_set.allocate(0xAAAA)
        print("\nFinal allocation - Tag 0xAAAA:")
        print(f"Selected way: {way}")
        print(
            f"PLRU state:   {self.cache_set.state:015b}"
        )  # Expected: 0b101_0110_1001_1101
        print(f"Victim tag:   {hex(victim_line.tag) if victim_line else None}")

        # Verify the final allocation
        self.assertEqual(way, 12)  # Should use way 12
        self.assertIsNotNone(victim_line)  # Should have a victim
        self.assertEqual(victim_line.tag, 0xC)  # Victim should have tag 0xC


if __name__ == "__main__":
    unittest.main(verbosity=2)
