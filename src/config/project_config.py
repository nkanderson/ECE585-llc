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


def parse_arguments():
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
        "-f", "--file", type=str, help="Path to the trace file to process", default=None
    )
    parser.add_argument(
        "-s", "--silent", action="store_true", help="Reduce program output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    return parser.parse_args()


def initialize():
    """Set up configurations that depend on runtime conditions."""
    # Declare globals so these can be accessed at the module level
    global args, logger
    args = parse_arguments()

    if args.silent:
        loglevel = LogLevel.SILENT
    else:
        loglevel = LogLevel.DEBUG if args.debug else LogLevel.NORMAL

    # Create an instance of the logger to be shared across files
    logger = CacheLogger(loglevel)


initialize()
