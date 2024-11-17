import math
from typing import List, NamedTuple, Optional

from cache_set import CacheLine, CacheSetPLRUMESI

from common.constants import LogLevel, MESIState
from config.project_config import config  # Import global config object
from utils.statistics import Statistics


class AddressFields(NamedTuple):
    """Immutable container for address decomposition fields"""

    tag: int
    index: int
    byte_select: int


class Cache:
    """
    Implementation of a set-associative cache with MESI protocol and PLRU replacement.
    Sets are created lazily as they are accessed to optimize memory usage, but stored
    in a list for direct indexed access.

    Architecture:
        This class implements a multi-level cache hierarchy where:
        - Cache sets are stored in a list but initialized as None
        - Sets are created on-demand when first accessed
        - Each set contains multiple ways (CacheLine instances)
        - Each line maintains MESI coherence state and L1 inclusion status
    """

    def __init__(self):
        """
        Initialize cache configuration
        Args:
            config: Optional CacheConfig instance. If None, creates new instance.
        """
        # Load configuration
        self.config = config.get_cache_config()
        # Load Logger
        self.logger = config.get_logger()
        self.statistics = Statistics()

        # Set cache parameters from config
        self.line_size = self.config.line_size
        self.associativity = self.config.associativity
        self.total_capacity = self.config.total_capacity

        # Calculate number of sets
        self.num_sets = self.total_capacity // (self.line_size * self.associativity)

        # Validate cache parameters
        if not math.log2(self.line_size).is_integer():
            raise ValueError("Block size must be power of 2")
        if not math.log2(self.num_sets).is_integer():
            raise ValueError("Number of sets must be power of 2")

        # Calculate address decomposition bits (assume 32 bit address)
        self.byte_select_bits = int(math.log2(self.line_size))
        self.index_bits = int(math.log2(self.num_sets))
        self.tag_bits = 32 - self.index_bits - self.byte_select_bits

        # Initialize list with None placeholders for sets
        self.sets: List[Optional[CacheSetPLRUMESI]] = [None] * self.num_sets

        # Track number of allocated sets
        self.allocated_sets = 0

        # Dump cache configuration to logger in debug mode
        self.logger.log(LogLevel.DEBUG, message=self.__config_str)

    def __decompose_address(self, address: int) -> AddressFields:
        """
        Internal Method to address into tag, index and byte_select fields
        Args:
            address: Full memory address
        Returns:
            AddressFields object containing decomposed fields
        """
        byte_select_mask = (1 << self.byte_select_bits) - 1
        index_mask = (1 << self.index_bits) - 1

        byte_select = address & byte_select_mask
        index = (address >> self.byte_select_bits) & index_mask
        tag = address >> (self.byte_select_bits + self.index_bits)

        return AddressFields(tag=tag, index=index, byte_select=byte_select)

    def pr_read(self, address: int) -> bool:
        """Processor side read request to the cache"""
        self.statistics.record_read()
        # Decompose 32-bit address into tuple of tag, index, byte_select
        addr_fields = self.__decompose_address(address)

        if self.sets[addr_fields.index] is None:
            self.statistics.record_miss()
            # Allocate newly reference set
            self.sets[addr_fields.index] = self.__create_set()
            return False  # MISS

        # Obtain cache set instance
        cache_set = self.sets[addr_fields.index]
        # Perform read search for tag in set
        is_hit = cache_set.pr_read(addr_fields.tag)

        if is_hit:  # HIT
            self.statistics.record_hit()
        else:  # MISS
            self.statistics.record_miss()

        return is_hit

    def pr_write(self, address: int) -> bool:
        """Process side write request to the cache"""
        self.statistics.record_write()
        addr_fields = self.__decompose_address(address)

        if self.sets[addr_fields.index] is None:
            self.statistics.record_miss()
            # Allocate newly reference set
            self.sets[addr_fields.index] = self.__create_set()
            return False  # MISS

        cache_set = self.sets[addr_fields.index]
        is_hit = cache_set.pr_write(addr_fields.tag)

        if is_hit:
            self.statistics.record_hit()
            return True  # HIT
        else:
            self.statistics.record_miss()
            return False  # MISS

    def cache_line_fill(self, address: int, state: MESIState) -> Optional[CacheLine]:
        """Fill a cache line with data and set MESI state
        This would called after a cache miss to fill the cache line with data

        TODO: We may need to add inclusivity checks here, after all all cache
        line fills would come from L1 Cache

        Args:
            address: Memory address to fill
            state: MESI state to set

        Returns:
            Optional[CacheLine]: CacheLine object is return if PLRU replacement
            found a cache line to replace, or None if set not full. Returned victim
            my need to be written back to memory if a modified line.
        """
        addr_fields = self.__decompose_address(address)
        # This should never be None, as we should have allocated the set on miss
        if self.sets[addr_fields.index] is None:
            self.sets[addr_fields.index] = self.__create_set()

        cache_set = self.sets[addr_fields.index]
        # Return the replaced cache line if set is full
        return cache_set.allocate(addr_fields.tag, state)

    def __create_set(self) -> CacheSetPLRUMESI:
        """
        Internal method to create a new cache set dynamically
        """
        return CacheSetPLRUMESI(num_ways=self.associativity)

    def get_line_state(self, address: int) -> Optional[MESIState]:
        """
        Get the MESI state of the cache line containing the address

        Args:
            address: Memory address to check
        Returns:
            MESIState if line exists, None if line not in cache
        """
        addr_fields = self.__decompose_address(address)

        # Return None if set doesn't exist yet
        if self.sets[addr_fields.index] is None:
            return None

        cache_set = self.sets[addr_fields.index]
        way_index = cache_set.find_way_by_tag(addr_fields.tag)

        if way_index is not None:
            return cache_set.mesi_state[way_index]
        return None

    def set_line_state(self, address: int, state: MESIState) -> bool:
        """
        Setter method to modify the MESI state of a cache line

        Args:
            address: Memory address to modify
            state: New MESI state to set
        Returns:
            True if line exists and state was set, False if line not in cache
        Raises:
            ValueError: If invalid state transition attempted
        """
        addr_fields = self.__decompose_address(address)

        if self.sets[addr_fields.index] is None:
            return False

        cache_set = self.sets[addr_fields.index]
        way_index = cache_set.find_way_by_tag(addr_fields.tag)

        if way_index is not None:
            try:
                cache_set.mesi_state[way_index] = state
                return True
            except ValueError as e:
                raise ValueError(
                    f"Invalid state transition for address {hex(address)}: {e}"
                )
        return False

    def clear_cache(self):
        """Clear all cache contents and reset statistics"""
        self.sets = [None] * self.num_sets
        self.allocated_sets = 0

    def print_cache(self):
        """Print cache contents of only valid lines"""
        for index, cache_set in enumerate(self.sets):
            if cache_set is not None:
                self.sets[index].print_set()

    @property
    def __config_str(self) -> str:
        """Generate string representation of cache configuration"""
        return f"""
----------------------------------
Cache Configuration
----------------------------------
Total Cache Capacity: {self.total_capacity/2**20:.2f} MB
Line Size: {self.line_size} bytes
Associativity: {self.associativity}-way
Number of Sets: {self.num_sets}
Address Bits:
    Tag: {self.tag_bits}
    Index: {self.index_bits}
    Byte Select: {self.byte_select_bits}
"""