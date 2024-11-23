from typing import Optional

from common.constants import CacheMessage, LogLevel
from config.project_config import config
from utils.cache_logger import CacheLogger


class L1Interface:
    """
    Handles all communication between L2 (LLC) and L1 cache for
    cache inclusivity
    """

    def __init__(self, logger: Optional[CacheLogger] = None):
        # FIXME: Need lazy initialization or some other solution to wait
        # until config has intialized the logger
        # self.logger = logger if logger is not None else config.get_logger()
        self.logger = logger if logger is not None else CacheLogger(LogLevel.DEBUG)

    def message_to_cache(self, message: CacheMessage, address: int) -> None:
        """Send control message to L1 cache"""
        self.logger.log(LogLevel.DEBUG, f"L2: {message.name}, Address: {address}")


_l1_interface = L1Interface()


def message_to_l1_cache(message: CacheMessage, address: int) -> None:
    _l1_interface.message_to_cache(message, address)
