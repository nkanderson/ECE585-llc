"""
ECE 585, Fall 2024
Last Level Cache Simulation Program

Authors: Niklas Anderson, Reece Wayt, Dan Engler, and Matthew Hardenburgh
Date: November, 2024
Description: This program simulates the behavior of a 16MB, 16-way set associative last level cache.
"""

from common.constants import LogLevel
from config.project_config import args, logger
from utils.event_handler import handle_event
from utils.trace_parser import TraceFileParser


def main():
    """
    Main entry point of the LLC Simulation program.
    """
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
                # TODO: Update Stats instance with these values, once we
                # decide where that instance lives
                stats_changes = handle_event(op.value)
                logger.log(
                    LogLevel.DEBUG,
                    f"Updating stats with the following: {stats_changes}",
                )
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
