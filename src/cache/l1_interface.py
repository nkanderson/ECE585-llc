from typing import Optional

from common.constants import CacheMessage, LogLevel
from config.project_config import config
from utils.cache_logger import CacheLogger


class L1Interface:
    """
    Handles all communication between L2 (LLC) and L1 cache for
    cache inclusivity
    """

    _l1_instance = None

    def __init__(self, logger: Optional[CacheLogger] = None):
        self.logger = logger if logger is not None else config.get_logger()

    @classmethod
    def initialize(cls, logger: CacheLogger):
        if cls._l1_instance is None:
            cls._l1_instance = cls(logger)

    @classmethod
    def get_instance(cls):
        if cls._l1_instance is None:
            raise RuntimeError("L1Interface instance is not initialized")
        return cls._l1_instance

    def message_to_cache(self, message: CacheMessage, address: int) -> None:
        """Send control message to L1 cache"""
        self.logger.log(
            LogLevel.NORMAL, f"L2: {message.name}, Address: 0x{address:08X}"
        )


def message_to_l1_cache(message: CacheMessage, address: int) -> None:
    L1Interface.get_instance().message_to_cache(message, address)
