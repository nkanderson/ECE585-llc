# Test Plan for CacheSet

## Overview
- This test plan covers the verification of the CacheSet class. The main responsibilities of the CacheSet is to store and maintain n-ways of CacheLine Data Classes. Replacement or eviction of a CacheLine is determine by the PLRU algorightm. The CacheSet also implements MESI protocol state tracking for cache coherency.  

**Note: that MESI protocol and state transistion are not part of this test set. Also, a default 16-way set is tested, although CacheSet support n-ways** 

## Running Tests
```bash
╭─  Linux 11:23 ~/S/P/ECE585-llc 
│ on  feature/cache-class [!?] 🐍 v3.12.7 
╰─❯ PYTHONPATH=./src python -m unittest tests.cache.test_cache_set -v
```



## Test Cases and Results

### 1. Constructor Validation Tests (test_constructor_validation)
* Purpose: Verify constructor properly validates num_ways parameter
* Test cases:
  - Valid ways: [1, 2, 4, 8, 16, 32]
  - Invalid types: float (2.5), string ("16")
  - Invalid ranges: 0, 33, -1
  - Non-power-of-2: 3
* Status: ✅ PASS

### 2. Initial State Tests (test_initial_state)
* Purpose: Verify initial state of newly created cache set
* Test cases:
  - Verify 16 ways created
  - Verify PLRU state = 0
  - Verify all lines invalid
  - Verify all tags None
* Status: ✅ PASS

### 3. PLRU Behavior Tests
#### 3.1 Basic PLRU Updates (test_plru_update)
* Purpose: Verify basic PLRU bit pattern updates
* Test sequence:
  - Access way 0: 0b000_0000_0000_0000
  - Access way 1: 0b000_0000_1000_0000
  - Access way 8: 0b000_0000_1000_0001
  - Access way 15: 0b100_0000_1100_0101
* Status: ✅ PASS

#### 3.2 Complex PLRU Pattern (test_plru_behavior)
* Purpose: Verify PLRU behavior for complex access patterns
* Test cases:
  1. Sequential Access to All Ways (0-15)
  2. Follow-up accesses to ways 8 and 2
  3. Verify final state: 0b111_0110_1101_1000
* Status: ✅ PASS

### 4. Cache Operations Tests
#### 4.1 Read Operations (test_read_operations)
* Purpose: Verify read hits/misses
* Test cases:
  - Read miss on empty cache
  - Read hit after allocation
  - Read miss on different tag
* Status: ✅ PASS

#### 4.2 Write Operations (test_write_operations)
* Purpose: Verify write hits/misses
* Test cases:
  - Write miss on empty cache
  - Write hit after allocation
  - Write miss on different tag
* Status: ✅ PASS

#### 4.3 Allocation Sequence (test_plru_allocation_sequence)
* Purpose: Verify realistic allocation sequence
* Test sequence:
  1. Sequential allocation (ways 0-15)
  2. Access ways 8 and 2
  3. Final allocation verifying:
     - Correct victim selection (way 12)
     - Proper victim tag (0xC)
     - Expected PLRU state
* Status: ✅ PASS

#### 4.4 Print Valid Cache Lines (test_print_set)
* Purpose: Verify print method only prints valid lines, skips invalid ones
* Test Sequence: 
  1. Load CacheSet with Valid and Invalid Lines
  2. Print CacheSet and perform visual analysis on STDOUT
* Status: ✅ PASS

#### 4.5 Perform Linear Search of Cache Set (find_way_by_tag)
* Purpose: Verify CacheSet way index can be found by tag bits. This is helpful using the getter and setter methods of the MESI bits
* Test Sequence: 
  1. Load CacheSet with lines
  2. Search for those lines by tag 
  3. Confirm returned index matches expected result
* Status: ✅ PASS

#### 4.6 Test getter and setter of MESI Descriptor (test_mesi_state_descriptor)
* Purpose: Verify that getter and setter method provide controlled access to cache line attributes
* Test Sequence: 
 1. Set MESI Bits with setter method
 2. Get MESI Bits with getter method
 3. Assert MESI Bits equal expected result
* Status: ✅ PASS

## Test Coverage Summary
- Total Tests: 7
- Passed: 7
- Failed: 0
- Test Duration: 0.001s

## Key Verifications
1. ✅ Constructor parameter validation
2. ✅ Initial state correctness
3. ✅ PLRU bit pattern accuracy
4. ✅ Cache operation functionality
5. ✅ Replacement policy correctness
6. ✅ Error handling
7. ✅ MESI Getter and Setter Methods

## Notes
- All PLRU state transitions are verified using binary pattern matching
- Test output includes detailed state information for debugging see below
```bash
╭─  Linux 17:30 ~/S/P/ECE585-llc/src 
│ on  feature/cache-set [!+] 🐍 v3.12.7 
╰─❯ python -m unittest tests.cache.tests_cache_set -v
test_constructor_validation (tests.cache.tests_cache_set.TestCacheSet.test_constructor_validation)
Test constructor parameter validation ... ok
test_initial_state (tests.cache.tests_cache_set.TestCacheSet.test_initial_state)
Test initial state of newly created cache set ... ok
test_plru_allocation_sequence (tests.cache.tests_cache_set.TestCacheSet.test_plru_allocation_sequence)
Test PLRU behavior during a realistic allocation sequence. ... 
Allocation 0 - Tag 0x0:
Selected way: 0
PLRU state:   000000000000000

Allocation 1 - Tag 0x1:
Selected way: 1
PLRU state:   000000010000000

Allocation 2 - Tag 0x2:
Selected way: 2
PLRU state:   000000010001000

Allocation 3 - Tag 0x3:
Selected way: 3
PLRU state:   000000110001000

Allocation 4 - Tag 0x4:
Selected way: 4
PLRU state:   000000110001010

Allocation 5 - Tag 0x5:
Selected way: 5
PLRU state:   000001110001010

Allocation 6 - Tag 0x6:
Selected way: 6
PLRU state:   000001110011010

Allocation 7 - Tag 0x7:
Selected way: 7
PLRU state:   000011110011010

Allocation 8 - Tag 0x8:
Selected way: 8
PLRU state:   000011110011011

Allocation 9 - Tag 0x9:
Selected way: 9
PLRU state:   000111110011011

Allocation 10 - Tag 0xa:
Selected way: 10
PLRU state:   000111110111011

Allocation 11 - Tag 0xb:
Selected way: 11
PLRU state:   001111110111011

Allocation 12 - Tag 0xc:
Selected way: 12
PLRU state:   001111110111111

Allocation 13 - Tag 0xd:
Selected way: 13
PLRU state:   011111110111111

Allocation 14 - Tag 0xe:
Selected way: 14
PLRU state:   011111111111111

Allocation 15 - Tag 0xf:
Selected way: 15
PLRU state:   111111111111111

Final allocation - Tag 0xAAAA:
Selected way: 12
PLRU state:   101011010011101
Victim tag:   0xc
ok
test_plru_behavior (tests.cache.tests_cache_set.TestCacheSet.test_plru_behavior)
Test of PLRU behavior using predefined test cases that ... 
Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 0 access:
Current state:  000000000000000
Expected state: 000000000000000

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 1 access:
Current state:  000000010000000
Expected state: 000000010000000

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 2 access:
Current state:  000000010001000
Expected state: 000000010001000

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 3 access:
Current state:  000000110001000
Expected state: 000000110001000

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 4 access:
Current state:  000000110001010
Expected state: 000000110001010

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 5 access:
Current state:  000001110001010
Expected state: 000001110001010

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 6 access:
Current state:  000001110011010
Expected state: 000001110011010

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 7 access:
Current state:  000011110011010
Expected state: 000011110011010

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 8 access:
Current state:  000011110011011
Expected state: 000011110011011

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 9 access:
Current state:  000111110011011
Expected state: 000111110011011

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 10 access:
Current state:  000111110111011
Expected state: 000111110111011

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 11 access:
Current state:  001111110111011
Expected state: 001111110111011

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 12 access:
Current state:  001111110111111
Expected state: 001111110111111

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 13 access:
Current state:  011111110111111
Expected state: 011111110111111

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 14 access:
Current state:  011111111111111
Expected state: 011111111111111

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 15 access:
Current state:  111111111111111
Expected state: 111111111111111

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 8 access:
Current state:  111011111011011
Expected state: 111011111011011

Sequential Access to All 16 Ways, then access 8, and 2 repectively - After way 2 access:
Current state:  111011011011000
Expected state: 111011011011000
ok
test_plru_update (tests.cache.tests_cache_set.TestCacheSet.test_plru_update)
Test PLRU bit updates after access (basic test) ... After way 0 access:
Current state:  000000000000000
Expected state: 000000000000000
After way 1 access:
Current state:  000000010000000
Expected state: 000000010000000
After way 8 access:
Current state:  000000010000001
Expected state: 000000010000001
After way 15 access: 
Current state:  100000011000101
Expected state: 100000011000101
ok
test_read_operations (tests.cache.tests_cache_set.TestCacheSet.test_read_operations)
Test cache read operations ... ok
test_write_operations (tests.cache.tests_cache_set.TestCacheSet.test_write_operations)
Test cache write operations ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.001s

OK


```
