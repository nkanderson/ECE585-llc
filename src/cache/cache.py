import math
import warnings
from typing import List, NamedTuple, Optional

from cache.bus_interface import bus_operation, put_snoop_result
from cache.cache_set import CacheLine, CacheSetPLRUMESI
from cache.l1_interface import message_to_l1_cache
from cache.mesi_controller import handle_processor_request, mesi_handle_snoop
from common.constants import BusOp, CacheMessage, LogLevel, MESIState, SnoopResult
from config.cache_config import CacheConfig
from config.project_config import config  # Import global config object
from utils.cache_logger import CacheLogger
from utils.statistics import Statistics


class AddressFields(NamedTuple):
    """Immutable container for address decomposition fields"""

    tag: int
    index: int
    byte_select: int


class Cache:
    """
    Description:
        Last Level Cache (LLC) class for use in a cache simulator

    Key Components:
        - This cache implements a write-allocate, write-back policy
        - 32-bit address decomposition into tag, index, and byte select fields
        - Set associative organization with PLRU replacement
        - MESI coherence protocol for multi-cache systems
        - Lazy set allocation (sets created only when first accessed)
        - Inclusion policy with L1 cache
        - Statistics tracking for cache hits, misses, and evictions

    Args:
        cache_config: Optional CacheConfig instance. If None, creates new instance.
        logger: Optional CacheLogger instance. If None, creates new instance.

    Example Usage:
        cache = Cache()
        # In response to trace command 0 or 2
        hit = cache.pr_read(0x1000)  # Processor read from address 0x1000
        # In response to trace command 1
        hit = cache.pr_write(0x2000) # Processor write to address 0x2000
        # In response to trace commands 3-6
        cache.handle_snoop(BusOp.READ, 0x1000)  # Process snoop from other cache
    """

    def __init__(
        self,
        cache_config: Optional[CacheConfig] = None,
        logger: Optional[CacheLogger] = None,
    ):
        """
        Constructs a cache class based on the provided configuration and logger see config and logger modules
        Default configurations is  64 MB, 64 B line size, 16-way associative, 32-bit address size
        """
        # Load configuration from optional argument or global config
        self.config = (
            cache_config if cache_config is not None else config.get_cache_config()
        )
        # Load Logger from optional argument or global config
        self.logger = logger if logger is not None else config.get_logger()
        self.statistics = Statistics()

        # Set cache parameters from config
        self.line_size = self.config.line_size
        self.associativity = self.config.associativity
        self.total_capacity = self.config.total_capacity  # In Bytes
        self.address_size = self.config.address_size  # In bits (defult 32)

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
        self.tag_bits = self.address_size - self.index_bits - self.byte_select_bits

        # Initialize list with None placeholders for sets
        self.sets: List[Optional[CacheSetPLRUMESI]] = [None] * self.num_sets

        # Dump cache configuration to logger in debug mode
        self.logger.log(LogLevel.DEBUG, message=self.__config_str)

    def __decompose_address(self, address: int) -> AddressFields:
        """
        Internal metho to break address into tag, index and byte_select fields
        Args:
            address: Full memory address
        Returns:
            AddressFields(NamedTuple)
        """
        byte_select_mask = (1 << self.byte_select_bits) - 1
        index_mask = (1 << self.index_bits) - 1

        byte_select = address & byte_select_mask
        index = (address >> self.byte_select_bits) & index_mask
        tag = address >> (self.byte_select_bits + self.index_bits)

        return AddressFields(tag=tag, index=index, byte_select=byte_select)

    def pr_read(self, address: int) -> bool:
        """Processor side read request"""
        hit = self.__processor_access(address, is_write=False)
        message_to_l1_cache(CacheMessage.SENDLINE, address)
        return hit

    def pr_write(self, address: int) -> bool:
        """Processor side write request"""
        hit = self.__processor_access(address, is_write=True)
        message_to_l1_cache(CacheMessage.SENDLINE, address)
        return hit

    def __processor_access(self, address: int, is_write: bool) -> bool:
        """
        Handle processor side cache access (read/write) in response to trace commands 0 and 1.

        Note:
            This method has side effects and should not be used for Cache Searches or Snoop
            operations; use lookup_line() or handle_snoop() methods, respectively.

        Args:
            address: Physical memory address to access
            is_write: True for write access, False for read access

        Side Effects:
            - Updates cache statistics
            - Handles cache misses and evictions
            - Handles MESI state transitions
            - Update PLRU bits on access

        Returns:
            bool: True if cache hit, False if miss
        """
        # Record statistics
        if is_write:
            self.statistics.record_write()
        else:
            self.statistics.record_read()

        addr_fields = self.__decompose_address(address)
        cache_set = self.sets[addr_fields.index]

        # Handle set allocation if needed
        if cache_set is None:
            self.statistics.record_miss()
            self.sets[addr_fields.index] = self.__create_set()
            new_state = handle_processor_request(
                current_state=MESIState.INVALID,
                address=address,
                is_processor_write=is_write,
            )
            self.cache_line_fill(address, new_state)
            return False

        # Search set and handle hit/miss
        way_index = cache_set.search_set(addr_fields.tag, update_plru=True)

        if way_index is not None:  # HIT
            current_state = cache_set.mesi_state[way_index]
            new_state = handle_processor_request(
                current_state=current_state,
                address=address,
                is_processor_write=is_write,
            )
            cache_set.mesi_state[way_index] = new_state
            self.statistics.record_hit()
            return True

        else:  # MISS
            new_state = handle_processor_request(
                current_state=MESIState.INVALID,
                address=address,
                is_processor_write=is_write,
            )
            victim_line = self.cache_line_fill(address, new_state)
            self.handle_victim_line(victim_line, address)
            self.statistics.record_miss()
            return False

    def cache_line_fill(self, address: int, state: MESIState) -> Optional[CacheLine]:
        """
        Fill a cache line with data and set MESI state. This would be called after a cache miss
        to fill the cache line with data. The method has run time warnings for invalid operations,
        to be presented to the user.

        Args:
            address: Memory address to fill
            state: MESI state to set

        Returns:
            Optional[CacheLine]: CacheLine object is return if PLRU replacement
            found a cache line to replace, or None if set not full. Returned victim
            my need to be written back to memory if a modified line.

        Raises:
            RuntimeWarning: If set is None or if line already exists
        """
        addr_fields = self.__decompose_address(address)
        # This should never be None, as we should have allocated the set on a miss
        cache_set = self.sets[addr_fields.index]
        if cache_set is None:
            warnings.warn(
                f"Cache set {addr_fields.index} was not allocated during a miss."
                "Creating set now...",
                RuntimeWarning,
            )
            self.sets[addr_fields.index] = self.__create_set()

        existing_line = self.lookup_line(address)
        if existing_line is not None:
            warnings.warn(
                f"Attempting to fill already existing line at address {hex(address)}."
                "Is this a replacement, if so use cache_set.allocate() for proper replacement."
                "Returning None...",
                RuntimeWarning,
            )
            return None

        cache_set = self.sets[addr_fields.index]
        # Allocate returns (victim_line, way_index) tuple, but we only need the victim line
        victim_line, _ = cache_set.allocate(addr_fields.tag, state)
        return victim_line

    def handle_snoop(self, bus_op: BusOp, address: int) -> None:
        """
        Handles operations for trace commands 3-6, which are snooped operations from other caches.

        returns:
            None
        """
        addr_fields = self.__decompose_address(address)

        cache_set = self.sets[addr_fields.index]

        if cache_set is None:
            # No need to handle snoop if this cache doesn't have copy
            put_snoop_result(address, SnoopResult.NOHIT)
            return

        way_index = cache_set.search_set(addr_fields.tag, update_plru=False)

        if way_index is not None:
            current_state = cache_set.mesi_state[way_index]
            new_state = mesi_handle_snoop(
                current_state=current_state, bus_op=bus_op, address=address
            )
            cache_set.mesi_state[way_index] = new_state
        else:
            put_snoop_result(address, SnoopResult.NOHIT)

    def handle_victim_line(
        self, victim_line: Optional[CacheLine], address: int
    ) -> None:
        """
        In the case of a cache line fill, a victim row may be returned if the set is full.
        This method handles the victim line by ensuring that modified data is written back to memory, and
        L1 inclusion is maintained.
        """
        if victim_line is None:  # No victim line to handle
            return

        if victim_line.is_modified():
            # Get most recent data from l1
            message_to_l1_cache(CacheMessage.GETLINE, address)
            message_to_l1_cache(CacheMessage.EVICTLINE, address)
            # Perform writeback for modified data
            bus_operation(BusOp.WRITE, address)

    def lookup_line(self, address: int) -> Optional[CacheLine]:
        """
        Look up a cache line and return a copy if present, without modifying cache state or statistics.
        Args:
            address: Memory address to check
        Returns:
            Optional[CacheLine]: Copy of the cache line if present, None if not cached
        """
        addr_fields = self.__decompose_address(address)

        # Return None if set doesn't exist yet
        if self.sets[addr_fields.index] is None:
            return None  # No need to allocate yet, not needed by this Cache

        cache_set = self.sets[addr_fields.index]
        way_index = cache_set.search_set(addr_fields.tag, update_plru=False)

        if way_index is not None:
            # Return a copy of the cache line to prevent accidental modifications
            line = cache_set.ways[way_index]
            return CacheLine(tag=line.tag, mesi_state=line.mesi_state)
        return None

    def __create_set(self) -> CacheSetPLRUMESI:
        """
        Internal method to create a new cache set dynamically
        """
        return CacheSetPLRUMESI(num_ways=self.associativity)

    def clear_cache(self):
        """
        Clear all cache contents and reset statistics, this is in response to trace command 8
        """
        self.sets = [None] * self.num_sets

    def print_cache(self):
        """Print cache contents of only valid lines using the logger, this is in response to trace command 9"""
        header_printed = False

        for index, cache_set in enumerate(self.sets):
            if cache_set is not None:
                # Get the formatted lines from print_set
                valid_lines = cache_set.print_set()
                if valid_lines:  # If there are valid lines to print
                    if not header_printed:
                        header = (
                            "\n-----------------------------"
                            "\nWay  | Tag      | MESI State|"
                            "\n-----------------------------"
                        )
                        self.logger.log(LogLevel.SILENT, header)
                        header_printed = True
                    self.logger.log(
                        LogLevel.SILENT, f"\nValid Lines in Set 0x{index:08x}"
                    )
                    self.logger.log(
                        LogLevel.SILENT, f"PLRU State Bits: {cache_set.state:b}"
                    )
                    self.logger.log(LogLevel.SILENT, "-----------------------------")
                    self.logger.log(LogLevel.SILENT, valid_lines)

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
