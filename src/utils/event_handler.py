from cache.cache import Cache
from common.constants import LogLevel
from config.project_config import config
from typing import Optional


def handle_event(
    cache: type[Cache], event_opcode: int, addr: Optional[int] = None
) -> None:
    """
    Processes a cache event based on the provided opcode and
    returns cache statistics for this event.

    Parameters:
        event_opcode (int): An integer (0-9) representing the cache event type.

    Returns:
        dict: A dictionary with cache statistics, including 'cache_reads', 'cache_writes',
              'cache_hits', and 'cache_misses'.
    """
    logger = config.get_logger()

    # Match on the event_opcode
    match event_opcode:
        # 0: read request from L1 data cache
        case 0:
            cache.pr_read(addr)
            logger.log(LogLevel.DEBUG, "read request from L1 data cache")

        # 1: write request from L1 data cache
        case 1:
            cache.pr_write(addr)
            logger.log(LogLevel.DEBUG, "write request from L1 data cache")

        # 2: read request from L1 instruction cache
        case 2:
            cache.pr_read(addr)
            logger.log(LogLevel.DEBUG, "read request from L1 instruction cache")

        # 3: snooped read request
        # 4: snooped write request
        # 5: snooped read with intent to modify request
        # 6: snooped invalidate command
        case 3 | 4 | 5 | 6:
            cache.handle_snoop(event_opcode, addr)
            logger.log(LogLevel.DEBUG, f"snooped request with code {event_opcode}")

        # 8: clear the cache and reset all state
        case 8:
            cache.clear_cache()
            logger.log(LogLevel.DEBUG, "clear the cache and reset all state")

        # 9: print contents and state of each valid cache line (doesn’t end simulation)
        case 9:
            cache.print_cache()
            logger.log(
                LogLevel.DEBUG, "print contents and state of each valid cache line"
            )

        # Default case (if opcode does not match any known command)
        case _:
            logger.log(LogLevel.DEBUG, f"Unknown opcode: {event_opcode}")
