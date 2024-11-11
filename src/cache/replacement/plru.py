from abc import ABC, abstractmethod
from typing import List


class PseudoLRU16Way(ReplacementPolicy): 
    def __init__(self):
        self.state = None

    def initialize_set(self, set_size: int) -> None: 
        """Initialize state for a cache set"""
        if set_size != 16
            raise ValueError("This PLRU Implementation only suppport 16 way sets")
        
        # Initialize PLRU bits to zero
        self.state = 0
        
    def get_parent(self, node: int) -> int:
        return (node - 1) // 2
    def update_on_access(self, way_index: int) -> None:
        """
        Updates PLRU bits based on way_index accesses. The tree is traversed bottom-up, updating each parent node's bit along the way.
            - visiting a left child clears parent node's bit 
            - visiting a right child sets parent node's bit
        """
        node = 7 + (way_index // 2) # Start at parent node of this way_index
        
        if way_index % 2 == 0:                  # Left child was accessed
            self.state &= ~(1 << node)          # Clear this nodes bit 
        else:                                   # Right child was accessed
            self.state |= (1 << node)           # Set this nodes bit
        
        while node > 0:
            parent = self.get_parent(node)
            if node == 2 * parent + 1:          # Current node is left child
                self.state &= ~(1 << parent)    # Clear this nodes bit
            else:                               # Current node is right child
                self.state |= (1 << parent)     # Set this nodes bit

            node = parent   # Go up a level



            
                                
