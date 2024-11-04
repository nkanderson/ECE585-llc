"""
Logger Utility
    Statistics: responsible for data storage and basic calculations
    CacheLogger: responsible for logging operations and updating statistics
"""
from dataclasses import dataclass
from functools import wraps
from typing import Callable

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

    def print_stats(self):
        """Print formatted cache statistics
        
        The statistics are left-aligned with consistent padding from labels.
        Format explanation:
            - :<8 means left-align in field of width 8
            - :<8.5% means left-align, show as percentage with 5 decimal places
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
        print(stats)

class CacheLogger(Statistics):
    """
    Custom logging system with three simple modes:
        1. silent  - Only show statistics and command 9 responses
        2. normal  - Show operations and stats
        3. debug   - Show everything including entry/exit of functions
    """
    def __init__(self, mode: str = 'normal'):
        super().__init__()
        if mode not in ['silent', 'normal', 'debug']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'silent', 'normal', or 'debug'")
        self.mode = mode

    def debug(self, message: str):
        """Print debug messages only in debug mode"""
        if self.mode == 'debug':
            print(f"DEBUG: {message}")

    def log(self, message: str):
        """Print operational messages in normal and debug modes"""
        if self.mode in ['normal', 'debug']:
            print(message)

    def force_log(self, message: str):
        """Print messages that should always show (stats and command 9)"""
        print(message)

    def record_read(self): 
        self.cache_reads += 1
        
    def record_write(self): 
        self.cache_writes += 1

    def record_hit(self): 
        self.cache_hits += 1

    def record_miss(self): 
        self.cache_misses += 1


def log_operation(logger: CacheLogger):
    """
    Generic decorator for logging cache operations with configurable logging levels.
    
    This decorator wraps cache operation functions to provide:
        1. Debug level entry/exit logging
        2. Normal level operation logging with formatted output
        3. Automatic statistic tracking
    
    How it works:
        @log_operation(logger=cache_logger)
        def BusOperation(self, BusOp: int, Address: int, SnoopResult: int):
            pass
            
        # When this code runs:
        simulator.BusOperation(BusOp.READ, 0x1234, NOHIT)
        
        # Here's he complete flow:
        # 1. Python sees @log_operation(logger=cache_logger) and calls log_operation
        # 2. log_operation returns the decorator function
        # 3. decorator wraps the original BusOperation and returns wrapper
        # 4. When BusOperation is called, wrapper actually executes:
        #    a. args captures (self, BusOp.READ, 0x1234, NOHIT)
        #    b. kwargs is empty {}
        #    c. func.__name__ gets "BusOperation" for logging
        #    d. Logger prints debug entry message
        #    e. Original BusOperation executes and returns value (e.g., True)
        #    f. result captures the return value from BusOperation
        #    g. Logger prints operation message
        #    h. Logger prints debug exit message with result
        #    i. wrapper returns result back through the chain to the caller
        # 5. Final result is available in the caller's scopet
    
    Args:
        logger (CacheLogger): Instance of CacheLogger to use for logging operations

    Returns:
        The decorator has multiple levels of returns:
        1. log_operation returns the decorator function
        2. decorator returns the wrapper function
        3. wrapper returns the result of the original function
    Note:
        The decorator preserves the original function's metadata through @wraps
        and provides different output based on the logger's mode (silent/normal/debug)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get operation name from the function name
            op_name = func.__name__
            
            # Debug level: entry logging
            logger.debug(f"Entering {op_name} with args={args[1:]} kwargs={kwargs}")
            
            # Execute the operation
            result = func(*args, **kwargs)
            
            # Normal level: operation logging
            # Format the output based on operation type
            if op_name == "BusOperation":
                logger.log(f"BusOp: {args[1]}, Address: {args[2]:x}, Snoop Result: {args[3]}")
            elif op_name == "PutSnoopResult":
                logger.log(f"SnoopResult: Address {args[1]:x}, SnoopResult: {args[2]}")
            elif op_name == "MessageToCache":
                logger.log(f"L2: {args[1]} {args[2]:x}")
            
            # Debug level: exit logging
            logger.debug(f"Exiting {op_name} with result: {result}")
            
            return result
        return wrapper
    return decorator
