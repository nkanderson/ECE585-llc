from abc import ABC, abstractmethod
from typing import Any, Optional

class ReplacementPolicy(ABC):
    """Abstract class for pluggable cache replacement policies"""
    @abstractmethod
    def initialize_set(self, set_size: int) -> None: 
        """Initialize state for a cache set
        
        Args: 
            set_size: Number of ways in the set
        """
        pass

    @abstractmethod
    def update_on_access(self, way_index: int) -> None: 
        """Update replacement state after an access

        Args: 
            way_index: Update based on which way was accesses
        """
        pass

    @abstractmethod
    def get_victim(self) -> int: 
        """Selects a cache line within a set to replace

        Returns:
            Index of the way to be replaced
        """
