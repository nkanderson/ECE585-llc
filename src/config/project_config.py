"""
Project Configuration and Constants
------------------------------------
This module contains global configuration settings and constants for the LLC Cache Simulator.

"""

import argparse
from pathlib import Path

from common.constants import LogLevel
from utils.cache_logger import CacheLogger

ROOT_DIR = Path(__file__).parents[1]

DATA_DIRECTORY = "data"
DEFAULT_TRACE_FILE = "trace.txt"


class Config:
    def __init__(self):
        self.args = None
        self.logger = None

    def get_args(self):
        """Return the parsed arguments."""
        return self.args

    def get_logger(self):
        """Return the logger instance."""
        return self.logger

    def initialize(self, args=None):
        """Set up configurations that depend on runtime conditions."""
        self.args = args = self.parse_arguments()
        if args.silent:
            loglevel = LogLevel.SILENT
        else:
            loglevel = LogLevel.DEBUG if args.debug else LogLevel.NORMAL

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
            "-s", "--silent", action="store_true", help="Reduce program output"
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="Enable debug output"
        )
        return parser.parse_args()


# Initialize a global config instance
config = Config()
