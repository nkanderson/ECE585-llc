from typing import Optional

from cache.cache import Cache
from common.constants import LogLevel
from config.project_config import config


def handle_event(
    cache: type[Cache], event_opcode: int, addr: Optional[int] = None
) -> None:
    """
    Processes a cache event based on the provided opcode and address.

    Parameters:
        cache: A Cache instance on which to perform the specified action.
        event_opcode (int): An integer (0-9) representing the cache event type.
        addr (int): An integer representing the target address in the cache

    """
    logger = config.get_logger()

    # Match on the event_opcode
    match event_opcode:
        # 0: read request from L1 data cache
        case 0:
            cache.pr_read(addr)

        # 1: write request from L1 data cache
        case 1:
            cache.pr_write(addr)

        # 2: read request from L1 instruction cache
        case 2:
            cache.pr_read(addr)

        # 3: snooped read request
        # 4: snooped write request
        # 5: snooped read with intent to modify request
        # 6: snooped invalidate command
        case 3 | 4 | 5 | 6:
            cache.handle_snoop(event_opcode, addr)

        # 8: clear the cache and reset all state
        case 8:
            cache.clear_cache()

        # 9: print contents and state of each valid cache line (doesn’t end simulation)
        case 9:
            cache.print_cache()

        # Default case (if opcode does not match any known command)
        case _:
            logger.log(LogLevel.DEBUG, f"Unknown opcode: {event_opcode}")
