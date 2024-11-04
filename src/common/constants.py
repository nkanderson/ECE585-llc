"""
Constnt definitions for the LLC simulator.
Includes operation types, results, and logging levels.
"""
from enum import IntEnum

class BusOp(IntEnum):
    """Bus Operation types as defined in project specs"""
    READ = 1        # Bus Read
    WRITE = 2       # Bus Write
    INVALIDATE = 3  # Bus Invalidate
    RWIM = 4        # Bus Read With Intent to Modify

class SnoopResult(IntEnum):
    """Snoop Result types as defined in project specs"""
    NOHIT = 0  # No hit
    HIT = 1    # Hit
    HITM = 2   # Hit to modified line

class CacheMessage(IntEnum):
    """L2 to L1 message types as defined in project specs"""
    GETLINE = 1        # Request data for modified line in L1
    SENDLINE = 2       # Send requested cache line to L1
    INVALIDATELINE = 3 # Invalidate a line in L1
    EVICTLINE = 4      # Evict a line from L1

class LogLevel(IntEnum):
    """Logging levels for the cache simulator
    
    Levels form a hierarchy where each level includes output from levels
    below it in numeric value:
        SILENT (0): Only statistics and command 9 responses
        NORMAL (1): Everything from SILENT + operation logs
        DEBUG  (2): Everything from NORMAL + debug info
    """
    SILENT = 0  # Base level
    NORMAL = 1  # Mid level
    DEBUG = 2   # Most verbose

class TraceCommand(IntEnum):
    """Trace file command types"""
    L1_DATA_READ = 0      # read request from L1 data cache
    L1_DATA_WRITE = 1     # write request from L1 data cache
    L1_INST_READ = 2      # read request from L1 instruction cache
    SNOOP_READ = 3        # snooped read request
    SNOOP_WRITE = 4       # snooped write request
    SNOOP_RWIM = 5        # snooped read with intent to modify
    SNOOP_INVALIDATE = 6  # snooped invalidate command
    CLEAR_CACHE = 8       # clear cache and reset all state
    PRINT_CACHE = 9       # print contents and state of valid linesa
