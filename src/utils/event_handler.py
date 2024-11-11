from common.constants import LogLevel
from config.project_config import logger


def handle_event(event_opcode: int) -> dict[str, int]:
    """
    Processes a cache event based on the provided opcode and
    returns cache statistics for this event.

    Parameters:
        event_opcode (int): An integer (0-9) representing the cache event type.

    Returns:
        dict: A dictionary with cache statistics, including 'cache_reads', 'cache_writes',
              'cache_hits', and 'cache_misses'.
    """
    cache_stats = {
        "cache_reads": 0,
        "cache_writes": 0,
        "cache_hits": 0,
        "cache_misses": 0,
    }

    # Match on the event_opcode
    # TODO: Logging event description should be replaced with desired
    # functionality for each event, and cache_stats should be updated
    # accordingly.
    match event_opcode:
        # 0: read request from L1 data cache
        case 0:
            logger.log(LogLevel.DEBUG, "read request from L1 data cache")

        # 1: write request from L1 data cache
        case 1:
            logger.log(LogLevel.DEBUG, "write request from L1 data cache")

        # 2: read request from L1 instruction cache
        case 2:
            logger.log(LogLevel.DEBUG, "read request from L1 instruction cache")

        # 3: snooped read request
        case 3:
            logger.log(LogLevel.DEBUG, "snooped read request")

        # 4: snooped write request
        case 4:
            logger.log(LogLevel.DEBUG, "snooped write request")

        # 5: snooped read with intent to modify request
        case 5:
            logger.log(LogLevel.DEBUG, "snooped read with intent to modify request")

        # 6: snooped invalidate command
        case 6:
            logger.log(LogLevel.DEBUG, "snooped invalidate command")

        # 8: clear the cache and reset all state
        case 8:
            logger.log(LogLevel.DEBUG, "clear the cache and reset all state")

        # 9: print contents and state of each valid cache line (doesn’t end simulation)
        case 9:
            logger.log(
                LogLevel.DEBUG, "print contents and state of each valid cache line"
            )

        # Default case (if opcode does not match any known command)
        case _:
            logger.log(LogLevel.DEBUG, f"Unknown opcode: {event_opcode}")

    # Return the dictionary with cache statistics
    return cache_stats
