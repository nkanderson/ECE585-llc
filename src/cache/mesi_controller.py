import warnings

from cache.bus_interface import bus_operation, get_snoop_result, put_snoop_result
from cache.l1_interface import message_to_l1_cache
from common.constants import BusOp, CacheMessage, MESIState, SnoopResult

# Color for warning messages
WARNING_COLOR = "\033[93m"  # Bright Yellow
RESET_COLOR = "\033[0m"  # Reset color to default


class MESICoherenceController:
    def handle_processor_request(
        self, current_state: MESIState, address: int, is_processor_write: bool = False
    ) -> MESIState:
        """
        Handles processor read request
        return: next state of the cacheline
        """

        if current_state == MESIState.INVALID and not is_processor_write:
            bus_operation(BusOp.READ, address)
            # Based on project requirements bus operation will return void, so
            # we need to check snoop result individual. TODO: Check if this is correct?
            snoop_result = get_snoop_result(address)
            if snoop_result in [SnoopResult.HIT, SnoopResult.HITM]:
                # Other cache will provide modified data, assume this happens automatically (per Mark's guidance)
                # Other LLC will flush the data, we will snarf it, making our state SHARED
                return MESIState.SHARED

            else:  # SnoopResult.NOHIT
                return MESIState.EXCLUSIVE

        elif (
            current_state in [MESIState.EXCLUSIVE, MESIState.SHARED, MESIState.MODIFIED]
            and not is_processor_write
        ):

            # No bus operation needed, stay in current state
            return current_state

        elif current_state == MESIState.INVALID and is_processor_write:
            bus_operation(BusOp.RWIM, address)  # Bus Read for ownership
            return MESIState.MODIFIED

        elif current_state == MESIState.SHARED and is_processor_write:
            bus_operation(BusOp.INVALIDATE, address)  # Bus Upgrade
            return MESIState.MODIFIED

        elif (
            current_state in [MESIState.MODIFIED, MESIState.EXCLUSIVE]
            and is_processor_write
        ):
            # No bus operation needed, move or stay in modified
            return MESIState.MODIFIED

        else:  # Default case for no state change, likely no possible case for this
            return current_state  # No state change

    def handle_snoop(
        self, current_state: MESIState, bus_op: BusOp, address: int
    ) -> MESIState:
        """Handle snooped bus operation from other LLCs"""
        if current_state == MESIState.INVALID:
            put_snoop_result(address, SnoopResult.NOHIT)
            return MESIState.INVALID

        if bus_op == BusOp.WRITE:  # Other LLC is writing to the address
            if current_state in [
                MESIState.SHARED,
                MESIState.EXCLUSIVE,
                MESIState.MODIFIED,
            ]:
                warnings.warn(
                    f"{WARNING_COLOR}Not possible WRITE-BACK operation on address"
                    f" {address:08x} in {current_state.name} state of our LLC{RESET_COLOR}",
                    RuntimeWarning,
                )
                # Ignore not possible WRITE-BACK operation return current state
                return current_state
            # else:
            return current_state  # NOP

        if current_state == MESIState.MODIFIED:
            if bus_op == BusOp.INVALIDATE:
                warnings.warn(
                    f"{WARNING_COLOR}Not possible bus upgrade command to modified line"
                    f" {address:08x} in {current_state.name} state of our LLC{RESET_COLOR}",
                    RuntimeWarning,
                )
                return current_state  # NOP

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
        put_snoop_result(address, SnoopResult.HITM)
        # Get most recent data from L1
        message_to_l1_cache(CacheMessage.GETLINE, address)
        # Perform writeback for modified data
        bus_operation(BusOp.WRITE, address)

        if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]:
            # We need to invalidate in L1
            message_to_l1_cache(CacheMessage.INVALIDATELINE, address)

    def __handle_clean_state_snoop(self, bus_op: BusOp, address: int) -> None:
        """Private helper method for when Cache Line is in SHARED or EXCLUSIVE state (i.e. CLEAN)"""
        # Signal Hit for clean states
        put_snoop_result(address, SnoopResult.HIT)

        if bus_op in [BusOp.RWIM, BusOp.INVALIDATE]:
            message_to_l1_cache(CacheMessage.INVALIDATELINE, address)


_mesi_coherence_controller = MESICoherenceController()


def handle_processor_request(
    current_state: MESIState, address: int, is_processor_write: bool = False
) -> MESIState:
    return _mesi_coherence_controller.handle_processor_request(
        current_state, address, is_processor_write
    )


def mesi_handle_snoop(
    current_state: MESIState, bus_op: BusOp, address: int
) -> MESIState:
    return _mesi_coherence_controller.handle_snoop(current_state, bus_op, address)
