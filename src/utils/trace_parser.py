from enum import IntEnum
from typing import Optional, Tuple
from src.config.project_config import ROOT_DIR, DEFAULT_TRACE_FILE

ROOT_DIR = Path(__file__).parents[2]     #Project Root Directory


class CacheSimOperation(IntEnum): 
    L1_DATA_READ = 0        # Read request from L1 data cache
    L1_DATA_WRITE = 1       # Rrite request from L1 data cache
    L1_INSTRUCTION_READ = 2 # Read request from L1 instruction cache
    SNOOPED_READ = 3        # Snooped read request 
    SNOOPED_WRITE = 4       # Snooped write request
    SNOOPED_READ_MODIFY = 5 # Snooped read with intent to modify request
    SNOOPED_INVALIDATE = 6  # Snooped invalidate command
    CLEAR_CACHE = 8         # Clear the cache and reset all state
    PRINT_CACHE = 9         # Print contents and state of each valid cache line
                            #    |- Does not end simulation

class TraceFileParser: 
    """Read's file default trace file or user provided file"""
    def __init__(self, filename: Optional[str] = None): 
        if filename is None: 
            self.filename = str(ROOT_DIR/DEFAULT_TRACE_FILE)
        else: 
            self.filename = filename


    def open(self) -> bool: 
        """Open the trace file""" 
        try: 
            self.file = open(self.filename, 'r') 
            return True
        except FileNoteFoundError: 
            print(f"[ERROR] - could not find trace file '{self.filename}'") 
            return False
        except Exception as e: 
            print(f"[ERROR] - Opening file: {e}")
            return False

    def close(self):
        if self.file:
            try: 
                self.file.close()
            except Exception as e:
                print(f"[ERROR] - Closing file: {e}") 

    def read_event(self) -> Optional[Tuple[CacheSimOperation, Optional[int]]]: 

    def __enter__(self):
        """Manager for entry to file""" 
        self.open()
        return self


    def __exit__(self):
        """Manager for exit of file""" 
        self.close()




