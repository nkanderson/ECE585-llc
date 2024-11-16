# Test Pln for Cache Logger

## Overview
This test plan covers the verification of the CacheLogger class and its decorator functionality. The CacheLogger is responsible for logging various cache operations with different levels of detail.

Running the unit test module
```bash
python -m unittest tests.utils.test_cache_logger
 #for more verbose results
python -m unittest -vv tests.utils.test_cache_logger
```

## Test Cases

### 1. Logging Levels Test
- Purpose: Verifies logger will properly handle logging based on its instantiated context level

#### 1.1. SILENT level only outputs to stdout and ignores NORMAL/DEBUG messages
#### 1.2. NORMAL level captures both SILENT and NORMAL messages, but ignores DEBUG
#### 1.3. DEBUG captures SILENT and NORMAL, plus more verbose output
#### 1.4. Check that message for NORMAL and DEBUG go to stderr

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

### 2. Bus Operation Logging Test
- Purpose: Validates the logging of cache bus operations
#### 2.1. Test BusOperation() Method
#### 2.2. Test GetSnoopResult() Method
#### 2.3. Test PutSnoopResult() Method
#### 2.4. Test MessageToCache
#### 2.5. Test Default Handler
#### Results
```bash
test_bus_operation_logging (tests.utils.test_cache_logger.TestCacheLogger.test_bus_operation_logging)
Test logging of bus operations ... ok
test_message_to_cache_logging (tests.utils.test_cache_logger.TestCacheLogger.test_message_to_cache_logging)
Test logging of cache messages ... ok
test_snoop_result_logging (tests.utils.test_cache_logger.TestCacheLogger.test_snoop_result_logging)
Test logging of snoop results ... ok
```
