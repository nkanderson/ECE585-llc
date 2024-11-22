"""
CacheSet: N-way Set Associative Cache with MESI Protocol and PLRU Replacement
-----------------------------------------------------------------------------
Author: Reece Wayt
Last Modified: May 2021
Description:
The CacheSet acts as a container for cache lines within a larger cache structure.
Parent cache class is expected to:
1. Handle address decomposition (tag, set index, offset)
2. Manage multiple CacheSet instances
3. Handle coherence protocol messages
4. Manage communication with upper/lower cache levels

Basic Operations:
------------------------------------------------------------------------------
- read(tag): Check if tag exists in set
- write(tag): Update existing line in set
- allocate(tag, state): Insert new line, potentially evicting existing line

MESI Protocol Support:
------------------------------------------------------------------------------
- Modified (M): Line is dirty and exclusive
- Exclusive (E): Line is clean and exclusive
- Shared (S): Line is clean and may exist in other caches
- Invalid (I): Line is unused/invalid

Note: Getting and Setting of MESI states is controlled by the MESIStateDescriptor class
    See Source - https://realpython.com/python-descriptors/

Replacement Policy:
------------------------------------------------------------------------------
Uses pseudo-LRU (tree-based) for selecting victim lines during allocation.
For n-way associative set, uses (n-1) bits to maintain binary tree state. Each node
in the tree is stored as a bit, with the following properties depending on operation:
    - Access Update:
        - If left child accessed, parent bit is cleared
        - If right child accessed, parent bit is set
    - Replacement Policy:
        - Follow tree path based on PLRU state to find victim line
        - Tree is traversed as a binary tree with (n-1) internal nodes
        - Leaf nodes represent cache ways, internal nodes are PLRU bits
        - Victim line is selected based on PLRU tree state
            - If bit is a 0, go right -> next_node = 2*node + 2
            - If bit is a 1, go left -> next_node = 2*node + 1
Constraints:
------------------------------------------------------------------------------
- num_ways must be power of 2 between MIN_WAYS and MAX_WAYS
- Each cache line tracks MESI state and L1 inclusion
- Parent cache must handle writebacks and inclusion policy

Note:
------------------------------------------------------------------------------
This implementation focuses on fundamental cache operations. Parent cache
class is responsible for more complex operations like snoop handling,
coherence messages, and inclusion enforcement.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from common.constants import MESIState


class MESIStateDescriptor:
    """
    Descriptor that provides (property-like) controlled access to MESI state of cache lines.
    This descriptor implements the Python descriptor protocol to provide a simple interface
    for accessing and modifying MESI states of cache lines within a cache set. It's used instead
    of traditional properties because it enables array-like indexing syntax for accessing specific
    cache ways.
    Usage:
        class CacheSetPLRUMESI:
            mesi_state = MESIStateDescriptor()
        # Getting state
        state = cache_set.mesi_state[way_index] # Returns MESIState enum
        # Setting state
        cache_set.mesi_state[way_index] = MESIState.MODIFIED
    """

    def __get__(self, obj, objtype=None):
        class StateAccessor:
            def __getitem__(self_, way_index: int) -> MESIState:
                """Get MESI state for a specific way"""
                if way_index < 0 or way_index >= obj.num_ways:
                    raise IndexError(f"Way index {way_index} out of range")
                return obj.ways[way_index].mesi_state

            def __setitem__(self_, way_index: int, state: MESIState):
                """Set MESI state for a specific way"""
                if way_index < 0 or way_index >= obj.num_ways:
                    raise IndexError(f"Way index {way_index} out of range")
                obj.ways[way_index].mesi_state = state

        return StateAccessor()


@dataclass
class CacheLine:
    """
    Represents a cache line with MESI protocol state tracking and L1 inclusion status.
    """

    tag: int = 0  # Tag value for the line
    mesi_state: MESIState = MESIState.INVALID

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

    def __str__(self) -> str:
        """String representation of the cache line"""
        return (
            f"Tag={hex(self.tag) if self.tag is not None else 'None'}, "
            f"State={self.mesi_state.name}. "
        )


class CacheSetPLRUMESI:
    """
    Implements an N-way set associative cache set with MESI protocol and PLRU replacement.
    Default configuration is 16-way, with supported ways from 1 to 32 (must be power of 2).
    """

    mesi_state = MESIStateDescriptor()  # Descriptor for MESI state access

    MAX_WAYS = 32  # Maximum supported ways
    MIN_WAYS = 1  # Minimum supported ways

    def __init__(self, num_ways: int = 16):
        # Validate num_ways
        if not isinstance(num_ways, int):
            raise TypeError("Number of ways must be an integer")
        if num_ways < self.MIN_WAYS or num_ways > self.MAX_WAYS:
            raise ValueError(
                f"Number of ways must be between {self.MIN_WAYS} and {self.MAX_WAYS}"
            )
        if not (num_ways & (num_ways - 1) == 0):
            raise ValueError("Number of ways must be a power of 2")

        self.num_ways = num_ways
        self.tree_levels = int(math.log2(num_ways))  # Levels in PLRU tree

        # Initialize cache lines
        self.ways = [CacheLine() for _ in range(num_ways)]

        # Initialize PLRU state - only need (num_ways - 1) bits for tree
        self.state = 0

    def __get_parent(self, node: int) -> int:
        """
        Helper method for PLRU tree traversal
            Args:
                node: current node index
            Returns:
              parent node of current node
        """
        return (node - 1) // 2

    def __update_plru(self, way_index: int) -> None:
        """
        Update PLRU state bits when a cache way is accessed. The PLRU tree is represented
        using (num_ways - 1) bits stored in self.state, where each bit represents a node
        in a binary tree.
            Tree Structure:
            - For n ways, we need (n-1) bits to represent internal nodes
            - Leaf nodes represent physical cache ways (0 to num_ways-1)
            - Internal nodes store PLRU bits that guide replacement decisions
            Example for 4-way cache:
                 0          <- Bit position in self.state
               /      /
              1       2       <- Bit positions in self.state
            /   /   /   /
           0    1  2    3    <- Physical way indices in self.ways[]

            Update Rules:
            - When accessing a left child: Clear parent's bit (0)
            - When accessing a right child: Set parent's bit (1)
            - Updates propagate up the tree (bottom up traveral) to maintain PLRU state

            Args:
                way_index: Physical index of the accessed cache way (0 to num_ways-1)
        """
        if way_index >= self.num_ways:
            raise ValueError(
                f"Way index {way_index} out of range for {self.num_ways}-way set"
            )

        # PLRU bits are updated with a bottom up tree traversal
        leaf_node = way_index + (
            self.num_ways - 1
        )  # Convert way index to a leaf_node number
        node = self.__get_parent(
            leaf_node
        )  # Use leaf node to get first internal node (i.e. PLRU bit)

        if way_index % 2 == 0:  # Left child accessed
            self.state &= ~(1 << node)  # Clear node's bit
        else:  # Right child accessed
            self.state |= 1 << node  # Set node's bit

        while node > 0:
            parent = self.__get_parent(node)
            if node == 2 * parent + 1:  # Current node is left child
                self.state &= ~(1 << parent)  # Clear parent's bit
            else:  # Current node is right child
                self.state |= 1 << parent  # Set parent's bit
            node = parent

    def __get_plru_victim(self) -> int:
        """
        Find the way to replace according to PLRU policy.
        Replacement Policy:
            - Follow tree path based on PLRU state to find victim line
                - If bit is a 0, go right -> next_node = 2*node + 2
                - If bit is a 1, go left -> next_node = 2*node + 1
            - Traverse until leaf nodes are reached, which represent cache ways
        Returns:
            Way index of the victim line from self.ways[]
                - way_index = node - (num_ways - 1)
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
        """
        Private Search Method: Find a cache line by tag.
            Returns (line, way_index) or (None, None)
        """
        for i, line in enumerate(self.ways):
            if not line.is_invalid() and line.tag == tag:
                return line, i
        return None, None

    def find_way_by_tag(self, tag: int) -> Optional[int]:
        """
        Find the way index containing a specific tag
        Args:
            tag: Tag to search for
        Returns:
            Way index if found, None if not found
        """
        for i, line in enumerate(self.ways):
            if not line.is_invalid() and line.tag == tag:
                return i
        return None

    def pr_read(self, tag: int) -> bool:
        """
        Simulates a processor side read request to a cache set. If tag is found returns HIT, else MISS.
        Upon a valid access plru bits are updated.
        """
        line, way_index = self.__find_line(tag)
        if line is not None:  # Hit
            # Update PLRU state bits on hit
            self.__update_plru(way_index)
            return True
        return False  # Miss

    def pr_write(self, tag: int) -> bool:
        """
        Simulates a processor side cache write request to a set. Write allocate policy is employed so any
        write misses require cache to allocate line.
        If tag is found returns HIT, else MISS.
        """
        line, way_index = self.__find_line(tag)
        if line is not None:  # Hit
            self.__update_plru(way_index)

            return True
        return False  # Miss, TODO: Implement write allocate logic, might be done by controller

    def allocate(
        self, tag: int, state: MESIState = MESIState.EXCLUSIVE
    ) -> Tuple[Optional[CacheLine], int]:
        """
        Allocate a new cache line. First searches for invalid lines
        if none found uses PLRU to select victim.
        Args:
            tag: Tag to be stored in the cache line
            state: Initial MESI state (default Exclusive for new allocations)

        Returns:
            (victim_line , allocated_way_index)
            - victim_line: CacheLine object of the victim line
            - If victim_line is None, no writeback needed (invalid line was used)
            - If victim_line is Modified, writeback needed
            - victim_line contains tag and L1 status for inclusion handling
        """
        # First check for invalid lines
        for way_index, line in enumerate(self.ways):
            if line.is_invalid():
                # Found an invalid line, use it
                line.tag = tag
                line.mesi_state = state
                self.__update_plru(way_index)
                return None, way_index
        # No invalid lines found, use PLRU to select victim
        victim_way = self.__get_plru_victim()
        victim_line = self.ways[victim_way]
        # Save victim info before overwriting
        victim_info = CacheLine(
            tag=victim_line.tag,
            mesi_state=victim_line.mesi_state,
        )
        # Set up new line
        victim_line.tag = tag
        victim_line.mesi_state = state
        # Update PLRU based on new line access
        self.__update_plru(victim_way)
        return victim_info, victim_way

    def print_set(self):
        """Prints only valid lines in the set"""
        if all(line.is_invalid() for line in self.ways):
            return  # Empty set

        print(
            f"\nPLRU State Bits: {self.state:b}"
            "\n-----------------------------"
            "\nWay  | Tag      | MESI State|"
            "\n-----------------------------"
        )
        line_format = "{:3d}  | 0x{:06x} | {:9s} |"

        for way_index, line in enumerate(self.ways):
            if not line.is_invalid():
                print(line_format.format(way_index, line.tag, line.mesi_state.name))

    @property
    def associativity(self) -> int:
        """Return the associativity (number of ways) of the set"""
        return self.num_ways
