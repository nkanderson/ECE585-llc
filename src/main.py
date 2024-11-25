"""
ECE 585, Fall 2024
Last Level Cache Simulation Program

Authors: Niklas Anderson, Reece Wayt, Dan Engler, and Matthew Hardenburgh
Date: November, 2024
Description: This program simulates the behavior of a 16MB, 16-way set associative last level cache.
"""

import sys

from cache.bus_interface import BusInterface
from cache.cache import Cache
from cache.l1_interface import L1Interface
from common.constants import LogLevel
from config.project_config import config
from utils.event_handler import handle_event
from utils.trace_parser import TraceFileParser


def main():
    """
    Main entry point of the LLC Simulation program.
    """
    # Initialize config with arguments from the command line
    config.initialize(sys.argv[1:])

    logger = config.get_logger()
    args = config.get_args()

    cache = Cache()

    BusInterface.initialize(logger)
    L1Interface.initialize(logger)

    try:
        with TraceFileParser(args.file) as parser:
            while True:
                result = parser.read_line()
                if result is None:
                    break
                op, addr = result
                logger.log(
                    LogLevel.DEBUG,
                    f"\nOperation: {op.value} {op.name:20} Address: 0x{addr:08x}",
                )
                handle_event(cache, op.value, addr)

    # Log a meaningful message and re-raise error to exit the program
    # with a non-zero exit code
    except ValueError as e:
        logger.log(LogLevel.DEBUG, f"[ERROR] - {str(e)}")
        raise
    except Exception as e:
        logger.log(LogLevel.DEBUG, f"[ERROR] - An unexpected error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
