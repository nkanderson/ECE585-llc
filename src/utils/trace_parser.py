from enum import IntEnum
from typing import Optional, Tuple
from src.config.project_config import ROOT_DIR, DEFAULT_TRACE_FILE

class CacheSimOperation(IntEnum): 
    L1_DATA_READ        = 0 # Read request from L1 data cache
    L1_DATA_WRITE       = 1 # Write request from L1 data cache
    L1_INSTRUCTION_READ = 2 # Read request from L1 instruction cache
    SNOOPED_READ        = 3 # Snooped read request 
    SNOOPED_WRITE       = 4 # Snooped write request
    SNOOPED_READ_MODIFY = 5 # Snooped read with intent to modify request
    SNOOPED_INVALIDATE  = 6 # Snooped invalidate command
    CLEAR_CACHE         = 8 # Clear the cache and reset all state
    PRINT_CACHE         = 9 # Print contents and state of each valid cache line

class TraceFileParser: 
    """Reads file default trace file or user provided file"""
    def __init__(self, filename: Optional[str] = None):  # Fix: init -> __init__
        self.fd = None  # Add this line to initialize fd
        if filename is None: 
            self.filename = str(ROOT_DIR/DEFAULT_TRACE_FILE)
        else: 
            self.filename = filename

    def open(self) -> bool: 
        """Open the trace file""" 
        try: 
            self.fd = open(self.filename, 'r', encoding="utf-8") 
            return True
        except FileNotFoundError:    
            print(f"[ERROR] - could not find trace file '{self.filename}'") 
            return False
        except Exception as e: 
            print(f"[ERROR] - Opening file: {e}")
            return False

    def close(self):
        """Close the trace file"""
        if self.fd:  # Fix: self.file -> self.fd
            try: 
                self.fd.close()  # Fix: self.file -> self.fd
            except Exception as e:
                print(f"[ERROR] - Closing file: {e}") 

    def read_line(self) -> Optional[Tuple[CacheSimOperation, Optional[int]]]: 
        line = self.fd.readline()
        if not line: # EOF, detects if line == ""
            self.close()
            print(f"[INFO] : Trace Read Complete")
            return None
        
        line = line.strip() 
        if not line: 
            return self.read_line()
            
        try: 
            parts = line.split()
            if len(parts) < 2: 
                print(f"[WARNING] : Invalid line read from trace, recursing to next line")
                return self.read_line()
                
            op = CacheSimOperation(int(parts[0]))
            addr = int(parts[1], 16)
            return op, addr
            
        except ValueError as e: 
            print(f"[WARNING] : Invalid line format : {line.strip()}")
            return self.read_line()
        except Exception as e: 
            print(f"[ERROR] : Couldn't parse line: {e}")
            return self.read_line()

    def __enter__(self):  # Fix: **enter** -> __enter__
        """Context manager for entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # Fix: Added proper parameters
        """Context manager for exit"""
        self.close()

if __name__ == "__main__":  # Fix: **name** -> __name__
    """Test the trace file parser utility"""
    with TraceFileParser() as parser:
        while True:
            result = parser.read_line()
            if result is None:
                break
            op, addr = result
            print(f"Operation: {op.name:20} Address: 0x{addr:08x}")
