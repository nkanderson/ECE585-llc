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
    def __init__(self):
        # If load_dotenv is None because no .env file is present,
        # load_config will check for values from the environment instead
        load_dotenv()
        self.load_config()

    def load_config(self):
        """
        Load configuration parameters from environment variables.
        Raises EnvironmentError if any required variable is missing.
        """
        capacity = os.getenv("CACHE_CAPACITY_MB")
        if capacity is None:
            raise EnvironmentError("CACHE_CAPACITY_MB not set in .env file")

        line_size = os.getenv("CACHE_LINE_SIZE_B")  # Fixed variable name
        if line_size is None:
            raise EnvironmentError("CACHE_LINE_SIZE_B not set in .env file")

        associativity = os.getenv("CACHE_ASSOCIATIVITY")
        if associativity is None:
            raise EnvironmentError("CACHE_ASSOCIATIVITY not set in .env file")

        protocol = os.getenv("CACHE_PROTOCOL")
        if protocol is None:
            raise EnvironmentError("CACHE_PROTOCOL not set in .env file")

        # Convert values
        self.total_capacity_mb = int(capacity)
        self.total_capacity = int(capacity) * 2**20  # Convert MB to bytes
        self.line_size = int(line_size)
        self.associativity = int(associativity)
        self.protocol = protocol


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
