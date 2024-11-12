from datalasses import dataclass
from typing import Optional, Tuple
import math

class MESIState(Enum):
    """
    Cache coherency states for the MESI protocol (2-bit encoding):
    
    M (Modified)  - Line is dirty and exclusive to this cache (0b11)
    E (Exclusive) - Line is clean and exclusive to this cache (0b10)
    S (Shared)    - Line is clean and may exist in other caches (0b01)
    I (Invalid)   - Line is invalid/unused (0b00)

    Source :  
        - https://en.wikipedia.org/wiki/MESI_protocol
    """
    INVALID = 0     # 0b00
    SHARED = 1      # 0b01
    EXCLUSIVE = 2   # 0b10
    MODIFIED = 3    # 0b11

    @property
    def bits(self) -> int:
        """Returns the 2-bit encoding of the state"""
        return self.value

@dataclass
class CacheLine:
    """
    Represents a cache line with MESI protocol state tracking and L1 inclusion status.
    """
    tag: Optional[int] = None
    mesi_state: MESIState = MESIState.INVALID
    in_l1: bool = False     # For cache coherency

    def is_invalid(self) -> bool:
        """Check if line is in Invalid state"""
        return self.mesi_state == MESIState.INVALID
    
    def is_shared(self) -> bool:
        """Check if line is in Shared state"""
        return self.mesi_state == MESIState.SHARED
    
    def is_exclusive(self) -> bool:
        """Check if line is in Exclusive state"""
        return self.mesi_state == MESIState.EXCLUSIVE
    
    def is_modified(self) -> bool:
        """Check if line is in Modified state"""
        return self.mesi_state == MESIState.MODIFIED
    
    def set_invalid(self):
        """Set line to Invalid state"""
        self.mesi_state = MESIState.INVALID
        
    def set_shared(self):
        """Set line to Shared state"""
        self.mesi_state = MESIState.SHARED
        
    def set_exclusive(self):
        """Set line to Exclusive state"""
        self.mesi_state = MESIState.EXCLUSIVE
        
    def set_modified(self):
        """Set line to Modified state"""
        self.mesi_state = MESIState.MODIFIED
    
    def get_state_bits(self) -> int:
        """Returns the 2-bit encoding of the current MESI state"""
        return self.mesi_state.bits

    def __str__(self) -> str:
        """String representation of the cache line"""
        return f"Tag={hex(self.tag) if self.tag is not None else 'None'}, " \
               f"State={self.mesi_state.name}, " \
               f"In L1={self.in_l1}"


class CacheSet:
    """
    Implements an N-way set associative cache set with MESI protocol and PLRU replacement.
    Default configuration is 16-way, with supported ways from 1 to 32 (must be power of 2).
    """
    MAX_WAYS = 32  # Maximum supported ways
    MIN_WAYS = 1   # Minimum supported ways

    def __init__(self, num_ways: int = 16):
        # Validate num_ways
        if not isinstance(num_ways, int):
            raise TypeError("Number of ways must be an integer")
        if num_ways < self.MIN_WAYS or num_ways > self.MAX_WAYS:
            raise ValueError(f"Number of ways must be between {self.MIN_WAYS} and {self.MAX_WAYS}")
        if not (num_ways & (num_ways - 1) == 0):
            raise ValueError("Number of ways must be a power of 2")
        
        self.num_ways = num_ways
        self.tree_levels = int(math.log2(num_ways))  # Levels in PLRU tree
        
        # Initialize cache lines
        self.ways = [CacheLine() for _ in range(num_ways)]
        
        # Initialize PLRU state - only need (num_ways - 1) bits for tree
        self.state = 0
        
    def __get_parent(self, node: int) -> int:
        """Helper method for PLRU tree traversal"""
        return (node - 1) // 2

    def __update_plru(self, way_index: int) -> None:
        """
        Update PLRU state when a way is accessed.
        """
        if way_index >= self.num_ways:
            raise ValueError(f"Way index {way_index} out of range for {self.num_ways}-way set")
            
        # PLRU bits are updated with a bottom up tree traversal
        leaf_node = way_index + (self.num_ways -1)  # Convert way index to a leaf_node number
        node = self.get_parent(leaf_node)           # Use leaf node to get first internal node (i.e. PLRU bit)

        if way_index % 2 == 0:                      # Left child accessed
            self.state &= ~(1 << node)              # Clear node's bit
        else:                                       # Right child accessed
            self.state |= (1 << node)               # Set node's bit
        
        while node > 0:
            parent = self.get_parent(node)
            if node == 2 * parent + 1:              # Current node is left child
                self.state &= ~(1 << parent)        # Clear parent's bit
            else:                                   # Current node is right child
                self.state |= (1 << parent)         # Set parent's bit
            node = parent
    
    def __get_plru_victim(self) -> int:
        """
        Find the way to replace according to PLRU policy.
        Returns: 
            - Way index [0 - n_ways]
        """
        node = 0
        for _ in range(self.tree_levels):           
            if self.state & (1 << node):
                node = 2 * node + 1  # Go left
            else:
                node = 2 * node + 2  # Go right
        # Calculate leaf node index based on number of ways
        return node - (self.num_ways - 1)
    
    def __find_line(self, tag: int) -> Tuple[Optional[CacheLine], Optional[int]]:
        """Find a cache line by tag. Returns (line, way_index) or (None, None)"""
        for i, line in enumerate(self.ways):
            if not line.is_invalid() and line.tag == tag:
                return line, i
        return None, None

    def read(self, tag: int) -> bool:
        """
        Simulates a read request to a cache set. If tag is found returns valid, else
        a cacheline fill is requested. Upon a valid access plru bits are updated. 
        """
        line, way_index = self.__find_line(tag)
        if line is not None:  # Hit
            self.__update_plru(way_index)
            return True
        return False          # Miss

    def write(self, tag: int) -> bool:
        """
        Simulates a cache write request to a set. Write allocate policy is employed so any 
        write misses require cache to allocate line. 
        """
        line, way_index = self.__find_line(tag)
        if line is not None:  # Hit
            self.__update_plru(way_index)
            
            return True
        return False          # Miss

    def allocate(self, tag: int, state: MESIState = MESIState.EXCLUSIVE) -> int:
        """
        Allocate a new cache line. First searches for invalid lines,
        if none found uses PLRU to select victim.
    
        Args:
            tag: Tag to be stored in the cache line
            state: Initial MESI state (default Exclusive for new allocations)
        
        Returns: 
         way_index where line was allocated
        """
        # First check for invalid lines
        for way_index, line in enumerate(self.ways):
            if line.is_invalid():
                # Found an invalid line, use it
                line.tag = tag
                line.mesi_state = state
                self.__update_plru(way_index)
                return way_index
            
        # No invalid lines found, use PLRU to select victim
        victim_way = self.__get_plru_victim()
        victim_line = self.ways[victim_way]
    
        # Set up new line
        victim_line.tag = tag
        victim_line.mesi_state = state
        victim_line.in_l1 = False  # Reset L1 inclusion status
    
        self.__update_plru(victim_way)
    return victim_way


    def __str__(self) -> str:
        """String representation showing valid lines"""
        output = []
        for i, line in enumerate(self.ways):
            if line['valid']:
                output.append(f"Way {i}: Tag={hex(line['tag'])}")
        return "\n".join(output) if output else "Empty Set"

   
    @property
    def associativity(self) -> int:
        """Return the associativity (number of ways) of the set"""
        return self.num_ways
