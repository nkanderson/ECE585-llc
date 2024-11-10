import sys
from dataclasses import dataclass
from typing import TextIO


@dataclass
class Statistics:
    """
    Simple data class used to store essential statistics for simulation.

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

    def record_read(self):
        """Record a cache read operation"""
        self.cache_reads += 1

    def record_write(self):
        """Record a cache write operation"""
        self.cache_writes += 1

    def record_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1

    def record_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1

    def print_stats(self, stream: TextIO = sys.stdout):
        """Print formatted cache statistics to specified stream
        Args:
            stream (TextIO): Output stream (defaults to sys.stdout)
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
        print(stats, file=stream, flush=True)  # flush avoids buffered output
