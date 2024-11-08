# Test Plan for Cache Logger

## Overview
This test plan covers the verification of the CacheLogger class and its decorator functionality. The CacheLogger is responsible for tracking cache statistics and logging various cache operations with different levels of detail.

Running the unit test module
```bash
 python -m unittest tests/utils/test_cache_logger.py

 #for more verbose results
 python -m unittest -vv tests/utils/test_cache_logger.py
```

## Test Cases

### 1. Statistics Tracking Test
- Purpose: Verifies logger correctly tracks basic cache statistics
#### 1.1. Test that each counter increments correctly
- Expected result: Each cache operation/result will increment there respective counters
	- cache_reads
	- cahce_writes
	- cache_hits
	- cache_misses
#### 1.2. Test that the hit ratio is calculated accurately
- Expected result: Cache hit ratio will dynamically calculate ratio
	- $$ cache_hits / (cache_hits + cache_misses) $$
### 1.3. Statistics Printing Test
- Expected result: The printed statistics will accurately and completely print the correct values as determined by the simulation events

#### Results of Test 1: 
- Printing confirmed for test 1.3 
```bash
Testing Statistics:

----------------------------------
          Cache Statistics
----------------------------------
  Number of cache reads:  100
  Number of cache writes: 50
  Number of cache hits:   75
  Number of cache misses: 25
  Cache hit ratio:        75.00000%
----------------------------------
```
- Assertion based checks pass for test 1.1 and 1.2
```bash
test_statistics_tracking (tests.utils.test_cache_logger.TestCacheLogger.test_statistics_tracking)
Test that statistics are properly tracked ... ok
```


### 2. Logging Levels Test
 - Purpose: Verifies logger will properly handle logging based on its instantiated context level

#### 2.1. SILENT level only outputs to stdout and ignores NORMAL/DEBUG messages
#### 2.2. NORMAL level captures both SILENT and NORMAL messages, but ignores DEBUG
#### 2.3. DEBUG captures SILENT and NORMAL, plus more verbose output. 
#### 2.4. Check that message for NORMAL and DEBUG go to stderr

#### Results
- Test passed for all levels, included use of stdout, stderr, and custom stream files. See debug.log, and stats.log for custom stream outputs. 
```bash
1. Testing Bus Operation logging:
DEBUG : Entering BusOperation with args=(<BusOp.READ: 1>, 4660, <SnoopResult.NOHIT: 0>) kwargs={}
DEBUG : Entering GetSnoopResult with args=(4660,) kwargs={}
NORMAL : GetSnoopResult: Address 1234, Snoop Result: HIT
DEBUG : Exiting GetSnoopResult with result: 1
NORMAL : BusOp: READ, Address: 1234, Snoop Result: NOHIT
DEBUG : Exiting BusOperation with result: None

2. Testing Snoop Result logging:
DEBUG : Entering GetSnoopResult with args=(22136,) kwargs={}
NORMAL : GetSnoopResult: Address 5678, Snoop Result: HIT
DEBUG : Exiting GetSnoopResult with result: 1
DEBUG : Entering PutSnoopResult with args=(39612, <SnoopResult.NOHIT: 0>) kwargs={}
NORMAL : SnoopResult: Address 9abc, SnoopResult: NOHIT
DEBUG : Exiting PutSnoopResult with result: None

3. Testing Cache Message logging:
DEBUG : Entering MessageToCache with args=(<CacheMessage.INVALIDATELINE: 3>, 57072) kwargs={}
NORMAL : L2: INVALIDATELINE def0
DEBUG : Exiting MessageToCache with result: None
```
- Assertion based tests passed as well 
```bash
test_logging_levels (tests.utils.test_cache_logger.TestCacheLogger.test_logging_levels)
Test that different logging levels work correctly ... ok
```

### 3. Bus Operation Logging Test
- Purpose: Validates the logging of cache bus operations
#### 3.1. Test BusOperation() Method
#### 3.2. Test GetSnoopResult() Method
#### 3.3. Test PutSnoopResult() Method
#### 3.4. Test MessageToCache
#### 3.4 Test Default Handler
#### Results
```bash
test_bus_operation_logging (tests.utils.test_cache_logger.TestCacheLogger.test_bus_operation_logging)
Test logging of bus operations ... ok
test_message_to_cache_logging (tests.utils.test_cache_logger.TestCacheLogger.test_message_to_cache_logging)
Test logging of cache messages ... ok
test_snoop_result_logging (tests.utils.test_cache_logger.TestCacheLogger.test_snoop_result_logging)
Test logging of snoop results ... ok
```
