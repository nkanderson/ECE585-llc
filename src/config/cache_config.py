"""
Cache Configuration Module
This module provides a configuration class for a cache memory system, with
parameters set via environment variables or command line arguments.
All configuration must be specified in .env file or via command line.

Command Line Usage:
    python cache_config.py --capacity 64 --line-size 64 --associativity 4 --protocol MESI

Required Environment Variables:
    CACHE_CAPACITY_MB: Total cache size in megabytes
    CACHE_LINE_SIZE_B: Size of each cache line in bytes
    CACHE_ASSOCIATIVITY: Number of ways in set-associative cache
    CACHE_PROTOCOL: Cache coherence protocol (MESI/MSI)
"""

import argparse
import os

from dotenv import load_dotenv


class CacheConfig:
    def __init__(
        self,
        total_capacity_mb=None,
        line_size=None,
        associativity=None,
        protocol=None,
        address_size=None,
    ):
        """
        Load cache configuration values.

        Precedence of values is as follows:
        - CacheConfig init arguments
        - environment variable (with .env loaded)
        - default value
        """
        # Attempt to load .env file
        load_dotenv()

        # Allow for user-provided values, but fall back to env vars or default
        self.total_capacity_mb = total_capacity_mb or self._get_env_var(
            "CACHE_CAPACITY_MB", 16
        )
        self.line_size = line_size or self._get_env_var("CACHE_LINE_SIZE", 64)
        self.associativity = associativity or self._get_env_var(
            "CACHE_ASSOCIATIVITY", 16
        )
        self.protocol = protocol or self._get_env_var("CACHE_PROTOCOL", "MESI")
        self.address_size = address_size or self._get_env_var("CACHE_ADDRESS_SIZE", 32)
        self.total_capacity = self.total_capacity_mb * 2**20  # Convert MB to bytes

    @staticmethod
    def _get_env_var(env_var_name, default_value):
        return type(default_value)(os.getenv(env_var_name, default_value))


"""
    ------------------------------END OF CLASS----------------------------------
    ----------------------------------------------------------------------------
"""
# --------------------------Small test for .env file usage-----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cache Configuration")
    parser.add_argument("--capacity", type=int, help="Cache capacity in MB")
    parser.add_argument("--line-size", type=int, help="Cache line size in bytes")
    parser.add_argument("--associativity", type=int, help="Cache associativity")
    parser.add_argument("--protocol", type=str, help="Cache protocol")

    args = parser.parse_args()

    # Override environment variables with command line arguments if provided
    if args.capacity:
        os.environ["CACHE_CAPACITY_MB"] = str(args.capacity)
    if args.line_size:
        os.environ["CACHE_LINE_SIZE_B"] = str(args.line_size)  # Fixed variable name
    if args.associativity:
        os.environ["CACHE_ASSOCIATIVITY"] = str(args.associativity)
    if args.protocol:
        os.environ["CACHE_PROTOCOL"] = args.protocol

    try:
        cache_config = CacheConfig()
        print(f"Cache Capacity: {cache_config.total_capacity/2**20} MB")
        print(f"Line Size: {cache_config.line_size} bytes")
        print(f"Associativity: {cache_config.associativity}-way")
        print(f"Protocol: {cache_config.protocol}")
    except EnvironmentError as e:
        print(f"Configuration Error: {e}")
