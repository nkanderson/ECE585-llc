"""
Project Configuration and Constants
------------------------------------
This module contains global configuration settings and constants for the LLC Cache Simulator.

"""

import argparse
from pathlib import Path

from common.constants import LogLevel
from config.cache_config import CacheConfig
from utils.cache_logger import CacheLogger

ROOT_DIR = Path(__file__).parents[1]

DATA_DIRECTORY = "data"
DEFAULT_TRACE_FILE = "trace.txt"


class Config:
    def __init__(self):
        # Leave these attributes uninitialized so the main function
        # can explicitly call initialize. This prevents issues with
        # imports in other modules during testing.
        self.args = None
        self.logger = None
        self.cache_config = None

    def get_args(self):
        """Return the parsed arguments."""
        return self.args

    def get_logger(self):
        """Return the logger instance."""
        return self.logger

    def get_cache_config(self):
        """Return the cache_config instance."""
        return self.cache_config

    def initialize(self, args=None):
        """Set up configurations that depend on runtime conditions."""
        # Create a new cache_config instance and load config from env vars.
        # These values can be overridden by command line options.
        self.cache_config = CacheConfig()
        self.cache_config.load_config()

        # Parse command line arguments, using env vars where relevant as defaults
        self.args = args = self.parse_arguments()
        if args.silent:
            loglevel = LogLevel.SILENT
        else:
            loglevel = LogLevel.DEBUG if args.debug else LogLevel.NORMAL

        # Update cache_config instance with user-provided values
        self.cache_config.total_capacity_mb = args.capacity
        self.cache_config.total_capacity = args.capacity * 2**20  # In bytes
        self.cache_config.line_size = args.line_size
        self.cache_config.associativity = args.associativity
        self.cache_config.protocol = args.protocol

        self.logger = CacheLogger(loglevel)

    def parse_arguments(self):
        """
        Parse command line arguments for the trace file parser.

        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = argparse.ArgumentParser(
            description="Cache Simulation Trace File Parser",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Path to the trace file to process",
            default=None,
        )
        parser.add_argument(
            "--capacity",
            type=int,
            help="Total last-level cache capacity in megabytes",
            default=self.cache_config.total_capacity_mb,
        )
        parser.add_argument(
            "--line_size",
            type=int,
            choices=[4, 16, 32, 64, 128],
            help="Size of each cache line in bytes",
            default=self.cache_config.line_size,
        )
        parser.add_argument(
            "--associativity",
            type=int,
            choices=[1, 2, 4, 8, 16, 32],
            help="Number of ways in set-associative cache",
            default=self.cache_config.associativity,
        )
        parser.add_argument(
            "--protocol",
            type=str,
            choices=["MESI", "MSI"],
            help="(NOTE: MSI option not yet implmented) Cache coherence protocol",
            default=self.cache_config.protocol,
        )
        parser.add_argument(
            "-s", "--silent", action="store_true", help="Reduce program output"
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="Enable debug output"
        )
        return parser.parse_args()


# Initialize a global config instance
config = Config()
