from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface
from common.constants import BusOp, CacheMessage, MESIState, SnoopResult


class MESICoherenceController:
    def __init__(self, bus_interface: BusInterface, l1_interface: L1Interface):
        self.bus = bus_interface
        self.l1 = l1_interface

    def handle_processor_request(
        self, current_state: MESIState, address: int, is_processor_write: bool = False
    ) -> MESIState:
        """
        Handles processor read request
        return: next state of the cacheline
        """
        # Based on project requirements bus operation will return void, so
        # we need to check snoop result individual. TODO: Check if this is correct?
        snoop_result = self.bus.get_snoop_result(address)

        if current_state == MESIState.INVALID and not is_processor_write:
            self.bus.bus_operation(BusOp.READ, address)

            if snoop_result in [SnoopResult.HIT, SnoopResult.HITM]:
                # Other cache will provide modified data, assume this happens automatically (per Mark's guidance)
                # Other LLC will flush the data, we will snarf it, making our state SHARED
                return MESIState.SHARED

            else:  # SnoopResult.NOHIT
                return MESIState.EXCLUSIVE

        elif current_state == MESIState.INVALID and is_processor_write:
            self.bus.bus_operation(BusOp.RWIM, address)  # Bus Read for ownership
            return MESIState.MODIFIED

        elif current_state == MESIState.SHARED and is_processor_write:
            self.bus.bus_operation(BusOp.INVALIDATE, address)  # Bus Upgrade
            return MESIState.MODIFIED

        elif current_state == MESIState.EXCLUSIVE and is_processor_write:
            # No bus operation needed, just update state
            return MESIState.MODIFIED

        else:  # current_state in [MESIState.SHARED, MESIState.MODIFIED, MESIState.EXCLUSIVE] && not is_processor_write
            return current_state  # No state change

    def handle_snoop(
        self, current_state: MESIState, bus_op: BusOp, address: int
    ) -> MESIState:
        """Handle snooped bus operation from other LLCs"""
        if current_state == MESIState.INVALID:
            self.bus.put_snoop_result(address, SnoopResult.NOHIT)
            return MESIState.INVALID

        if bus_op == BusOp.WRITE:  # Other LLC is writing to the address
            return current_state  # NOP

        if current_state == MESIState.MODIFIED:
            self.__handle_modified_state_snoop(bus_op, address)
            # Invalidate if other cache is modifying, otherwise downgrade to SHARED
            return (
                MESIState.INVALID
                if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]
                else MESIState.SHARED
            )

        if current_state in [MESIState.SHARED, MESIState.EXCLUSIVE]:
            self.__handle_clean_state_snoop(bus_op, address)
            # Invalidate if other cache is modifying, otherwise next state is SHARED
            return (
                MESIState.INVALID
                if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]
                else MESIState.SHARED
            )

        return current_state

    def __handle_modified_state_snoop(self, bus_op: BusOp, address: int) -> None:
        """Private helper method for when Cache Line is in MODIFIED state"""
        # Notify other cache that we have the data
        self.bus.put_snoop_result(address, SnoopResult.HITM)
        # Get most recent data from L1
        self.l1.message_to_cache(CacheMessage.GETLINE, address)
        # Perform writeback for modified data
        self.bus.bus_operation(BusOp.WRITE, address)

        if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]:
            # We need to invalidate in L1
            self.l1.message_to_cache(CacheMessage.INVALIDATELINE, address)

    def __handle_clean_state_snoop(self, bus_op: BusOp, address: int) -> None:
        """Private helper method for when Cache Line is in SHARED or EXCLUSIVE state (i.e. CLEAN)"""
        # Signal Hit for clean states
        self.bus.put_snoop_result(address, SnoopResult.HIT)

        if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]:
            self.l1.message_to_cache(CacheMessage.INVALIDATELINE, address)
