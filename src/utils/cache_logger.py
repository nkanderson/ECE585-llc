"""
Description: CacheLogging utility which handles simulated events and logs them based on each operation. 

Author: Reece Wayt

Sources: 
    - https://medium.com/@kuldeepkumawat195/python-print-flush-complete-guide-learn-today-f42f87cbc38c
    - https://realpython.com/primer-on-python-decorators/

""" 

from dataclasses import dataclass
from functools import wraps
from typing import Callable, TextIO
import sys
from src.common.constants import LogLevel, SnoopResult, BusOp, CacheMessage

@dataclass
class Statistics:
    """
    Simple data class used to store essential statistics for simulation. It is directly
    inherited by the CacheLogger as the Logger is responsible for maintaining, and reporting
    key statistics of the cache usage. 

    Attributes:
        cache_reads (int): Total number of read attempts to the cache
        cache_writes (int): Total number of write attempts to the cache
        cache_hits (int): Number of times requested data was found in cache
        cache_misses (int): Number of times requested data wasn't found in cache
    
    Note: 
     As a dataclass, this class automatically generates: 
        - __init__: The constructor method
        - __repr__: Defines string represention of object
        - __eq__: Enables equality comparison between instances

    Example:
        > stats = Statistics()
        > stats.cache_reads = 100
        > stats.cache_hits = 75
        > print(stats.cache_hit_ratio)
        0.75
    """
    cache_reads: int = 0
    cache_writes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0 

    @property
    def cache_hit_ratio(self) -> float: 
        """Dynamically calculates hit ratio"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0

    def print_stats(self, stream : TextIO = sys.stdout):
        """Print formatted cache statistics to specified stream
        Args: 
            stream (TextIO): Output stream (defaults to sys.stdout)

        """
        stats = f"""
----------------------------------
          Cache Statistics          
----------------------------------
  Number of cache reads:  {self.cache_reads:<10}
  Number of cache writes: {self.cache_writes:<10}
  Number of cache hits:   {self.cache_hits:<10}
  Number of cache misses: {self.cache_misses:<10}
  Cache hit ratio:        {self.cache_hit_ratio:<9.5%}
----------------------------------
"""
        print(stats, file=stream, flush=True) #flush avoids buffered output

class CacheLogger(Statistics):
    """
    Hierarchical logging system with statistics tracking and stream separation. 
    Silent logs go to stdout, while Normal and Debug logs go to stderr.

    Usage:
        # Basic usage (uses sys.stdout/stderr by default)
        > logger = CacheLogger(level=LogLevel.NORMAL)
        # Custom streams
        > with open('stats.log', 'w') as stdout, open('debug.log', 'w') as stderr:
        >   logger = CacheLogger(level=LogLevel.DEBUG, stdout=stdout, stderr=stderr)

    """
    def __init__(self, level: LogLevel = LogLevel.NORMAL,
                stdout: TextIO = sys.stdout,
                stderr: TextIO = sys.stderr):
        super().__init__()
        self.level = level
        self.stdout = stdout
        self.stderr = stderr

    def log(self, level: LogLevel, message: str):
        """
        Log message if level is sufficient

        Args: 
            level (LogLevel): Logging level of the message
            message (str): Message string
        Note:
            - Silent level messages go to stdout
            - Normal and Debug level messages go to stderr
        """
        if self.level >= level:
            stream = self.stdout if level == LogLevel.SILENT else self.stderr
            print(f"{level.name} : {message}", file=stream, flush=True) 

    #Statistics recording methods
    def record_read(self): self.cache_reads += 1
    def record_write(self): self.cache_writes += 1
    def record_hit(self): self.cache_hits += 1
    def record_miss(self): self.cache_misses += 1


def log_operation(logger: CacheLogger):
    """
    A decorator factory that creates function decorators for cache operation logging.
    
    This decorator implements a hierarchical logging system with configurable levels
    through the CacheLogger class. It uses closure to maintain logger state and
    wraps cache operations to add logging functionality without modifying their
    implementation.

    Logging Levels:
        1. Silent: Only outputs:
           - Summary statistics of cache usage
           - Responses to command 9 in trace files
        
        2. Normal (default): Outputs all Silent level items plus:
           - Bus operations
           - Snoop results
           - L2 to L1 cache communication messages
        
        3. Debug: Outputs all Normal level items plus:
           - Function entry/exit traces
           - Detailed argument logging
           - Return value logging

    Usage Example:
        ```python
        @log_operation(logger=cache_logger)
        def BusOperation(self, BusOp: int, Address: int, SnoopResult: int):
            # Function implementation
            pass

        # When called:
        simulator.BusOperation(BusOp.READ, 0x1234, NOHIT)
        # Will log based on logger's mode
        ```

    Implementation Flow:
        1. log_operation(logger): Creates closure with CacheLogger instance
        2. decorator(func): Takes the function to be decorated
        3. wrapper(*args, **kwargs): Handles the actual function call with logging

    Args:
        logger (CacheLogger): Logger instance that determines logging behavior
                            and maintains statistics

    Returns:
        Callable: A decorator function that will wrap the target function with
                 logging functionality

    Return Flow:
        1. log_operation returns: decorator function
        2. decorator returns: wrapper function
        3. wrapper returns: original function's result

    Technical Notes:
        - Uses @wraps from functools to preserve original function metadata
        - Accessing original function name via func.__name__ for logging
        - Args[1:] in debug logging skips 'self' parameter for cleaner output
        - Supports different output formats based on operation type
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get operation name from the function name
            op_name = func.__name__ 

            
            #Debug level logging
            logger.log(LogLevel.DEBUG, f"Entering {op_name} with args={args[1:]} kwargs={kwargs}")
            
            #Execute operation
            result = func(*args, **kwargs)
            
             match op_name:
                case "BusOperation":
                    # BusOp arg[1], Address arg[2], SnoopResult arg[3]
                    logger.log(LogLevel.NORMAL, 
                        f"BusOp: {BusOp(args[1]).name}, Address: {args[2]:x}, "
                        f"Snoop Result: {SnoopResult(args[3]).name}")
                
                case "GetSnoopResult":
                    # Address arg[1]
                    logger.log(LogLevel.NORMAL, 
                            f"GetSnoopResult: Address {args[1]:xi}, "
                            f"Snoop Result: {SnoopResult(result.name}")
                
                case "PutSnoopResult":
                    # Address arg[1], SnoopResult arg[2]
                    logger.log(LogLevel.NORMAL, 
                        f"SnoopResult: Address {args[1]:x}, "
                        f"SnoopResult: {SnoopResult(args[2]).name}")
                
                case "MessageToCache":
                     # Message arg[1], Address arg[2]
                    logger.log(LogLevel.NORMAL, 
                        f"L2: {CacheMessage(args[1]).name} {args[2]:x}")
                
                case _:  # Default case
                    logger.log(LogLevel.NORMAL, 
                            f"[ERROR] Logger could not find matching case for {op_name}, "
                            f"you should not be seeing this") 
                    pass

                                   
            # Debug level: exit logging
            logger.log(LogLevel.DEBUG, f"Exiting {op_name} with result: {result}")
            
            return result
        return wrapper
    return decorator
