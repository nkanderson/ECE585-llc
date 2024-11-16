# Cache Logger Documentaton

## Usage Guide

### Basic Setup
```python
from src.common.constants import LogLevel
from cache_logging import CacheLogger

# Default setup - uses stdout/stderr
logger = CacheLogger(level=LogLevel.NORMAL)

# Custom file streams
with open('stats.log', 'w') as stdout, open('debug.log', 'w') as stderr:
    logger = CacheLogger(
        level=LogLevel.DEBUG,
        stdout=stdout,
        stderr=stderr
    )
```

### Logging Levels
The logger supports three levels of verbosity:

1. **Silent** (`LogLevel.SILENT`)
   - Only outputs basic statistics and command 9 responses
   - All output goes to stdout
   - Best for production or when minimal logging is needed
   ```python
   logger = CacheLogger(level=LogLevel.SILENT)
   ```

2. **Normal** (`LogLevel.NORMAL`) - Default
   - Includes all Silent level outputs plus:
   - Bus operations
   - Snoop results
   - L2 to L1 cache communication messages
   - Operation-specific logs go to stderr
   ```python
   logger = CacheLogger(level=LogLevel.NORMAL)
   ```

3. **Debug** (`LogLevel.DEBUG`)
   - Includes all Normal level outputs plus:
   - Function entry/exit traces
   - Detailed argument logging
   - Return value logging
   - Debug information goes to stderr
   ```python
   logger = CacheLogger(level=LogLevel.DEBUG)
   ```

### Decorating Cache Operations
Use the `@log_operation` decorator to automatically log cache operations:

```python
@log_operation(logger=cache_logger)
def BusOperation(self, BusOp: int, Address: int, SnoopResult: int):
    # Function implementation
    pass
```


### Statistics Tracking

#### Current Implementation
The logger currently requires manual tracking of statistics:

```python
# Manual recording of operations
logger.record_read()
logger.record_write()
logger.record_hit()
logger.record_miss()

# Print statistics
logger.print_stats()  # Prints to stdout by default
logger.print_stats(stream=custom_file)  # Print to custom stream
```

#### TODO: Automatic Statistics Collection
The statistics tracking will be automated in a future update. The system will automatically track cache operations based on context without requiring manual recording.

```python
# Future implementation will automatically track statistics through the decorator
@log_operation(logger=cache_logger)
def read_cache(self, address: int):
    # Statistics will be automatically updated based on operation type
    # and return value without explicit calls to record_*() methods
    return cache_data

# Planned automatic detection for:
# - Operation type (read/write) from function context
# - Hit/miss status from return values or exceptions
# - Cache state changes from before/after operation comparison
```

#### Planned Features for Automatic Tracking:
1. **Context Detection**
   - Automatic identification of operation types
   - Pattern matching on function names and parameters
   - Return value analysis for hit/miss detection

2. **Operation Categories**
   ```python
   # Operation patterns to be automatically detected
   OPERATION_PATTERNS = {
       'read': ['read_cache', 'fetch', 'get'],
       'write': ['write_cache', 'store', 'put'],
       'hit': ['data_found', 'cache_hit'],
       'miss': ['data_not_found', 'cache_miss']
   }
   ```

3. **Automatic Updates**
   ```python
   # Example of planned automatic detection in log_operation
   def log_operation(logger: CacheLogger):
       def decorator(func: Callable) -> Callable:
           @wraps(func)
           def wrapper(*args, **kwargs):
               # TODO: Implement automatic operation detection
               # operation_type = detect_operation_type(func.__name__)
               # pre_state = capture_cache_state()
               
               result = func(*args, **kwargs)
               
               # TODO: Implement automatic statistics update
               # post_state = capture_cache_state()
               # update_statistics(logger, operation_type, pre_state, post_state, result)
               
               return result
           return wrapper
       return decorator
   ```

4. **State Tracking**
   - Pre/post operation state comparison
   - Cache line status monitoring
   - Access pattern analysis

Note: Until automatic tracking is implemented, continue using the manual recording methods. The transition to automatic tracking will be backward compatible.

### Custom Stream Handling
Redirect logs to different files:

```python
# Split logs between files
with open('statistics.log', 'w') as stats_file, \
     open('debug.log', 'w') as debug_file:
    
    logger = CacheLogger(
        level=LogLevel.DEBUG,
        stdout=stats_file,  # Silent logs (statistics)
        stderr=debug_file   # Normal and Debug logs
    )
```

