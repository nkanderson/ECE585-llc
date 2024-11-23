from typing import Optional

from common.constants import BusOp, LogLevel, SnoopResult
from config.project_config import config  # Global config object
from utils.cache_logger import CacheLogger


class BusInterface:
    """Handles all LLC-to-LLC bus operations and snoop results"""

    def __init__(self, logger: Optional[CacheLogger] = None):
        self.logger = logger if logger is not None else config.get_logger()

    def bus_operation(self, bus_op: BusOp, address: int) -> SnoopResult:
        """Simulate a bus operation and get snoop results from other caches"""
        snoop_result = self.get_snoop_result(address)
        self.logger.log(
            LogLevel.NORMAL,
            f"BusOp: {bus_op.name}, Address: {address}, Snoop Result: {snoop_result.name}",
        )

    def get_snoop_result(self, address: int) -> SnoopResult:
        """
        Simulate snoop results from other caches based on address LSBs:
        00 = HIT |  01 = HITM   | 10 or 11 = NOHIT
        Args:
            address: Memory address to check

        Returns:
            Appropriate snoop result based on address LSBs
        """
        # Get two least significant bits
        lsb = address & 0b11

        if lsb == 0b00:
            return SnoopResult.HIT
        elif lsb == 0b01:
            return SnoopResult.HITM
        else:  # 0b10 or 0b11
            return SnoopResult.NOHIT

    def put_snoop_result(self, address: int, snoop_result: SnoopResult) -> None:
        """Report our snoop result for operations from other caches"""
        self.logger.log(
            LogLevel.NORMAL,
            f"Address: {address:08x}, Snoop Result: {snoop_result.name}",
        )
