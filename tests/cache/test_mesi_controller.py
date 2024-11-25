import unittest
from unittest.mock import MagicMock, patch

from cache.bus_interface import BusInterface
from cache.l1_interface import L1Interface
from cache.mesi_controller import MESICoherenceController
from common.constants import BusOp, CacheMessage, MESIState, SnoopResult
from utils.cache_logger import CacheLogger


class TestMESIProtocol(unittest.TestCase):
    """
    Test suite for MESI protocol implementation in the LLC.
    """

    def setUp(self):
        """Setup up test environment before each test"""
        
        # Create mock logger
        self.mock_logger = MagicMock(spec=CacheLogger)
        self.mock_args = MagicMock(silent=False, debug=True)

        # Patch config to prevent real logger usage
        patch(
            "config.project_config.config.get_logger",
            return_value=self.mock_logger
        ).start()
        
        patch(
            "config.project_config.config.get_args",
            return_value=self.mock_args
        ).start()


        # Initialize both singletons, TODO: consider using mocking here too
        BusInterface.initialize(self.mock_logger)       
        L1Interface.initialize(self.mock_logger)


        # Setup patches for external dependencies
        # Note: We're patching the module-level functions, not the class methods
        self.bus_op_patcher = patch("cache.bus_interface.BusInterface.bus_operation")
        self.get_snoop_patcher = patch("cache.bus_interface.BusInterface.get_snoop_result")
        self.put_snoop_patcher = patch("cache.bus_interface.BusInterface.put_snoop_result")
        self.message_to_l1_patcher = patch("cache.l1_interface.L1Interface.message_to_cache")

        # Start all patches
        self.mock_bus_op = self.bus_op_patcher.start()
        self.mock_get_snoop = self.get_snoop_patcher.start()
        self.mock_put_snoop = self.put_snoop_patcher.start()
        self.mock_l1_message = self.message_to_l1_patcher.start()
        
        # Set default return value for get_snoop_result
        self.mock_get_snoop.return_value = SnoopResult.NOHIT

        # Create controller instance with mock logger and mock dependencies
        self.controller = MESICoherenceController()
    
        

    def tearDown(self):
        # Stop any patches done during the test
        BusInterface._bus_instance = None
        L1Interface._l1_instance = None
        patch.stopall()

    ############################################################################################################
    # Processor request tests

    def test_processor_read_invalid_and_nohit(self):
        """
        Test handling a processor read request for a cacheline in INVALID state and NOHIT snoop result
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.NOHIT

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.INVALID, address, is_processor_write=False)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.READ, 0x1000)

        # Check that the snoop result was checked
        self.mock_get_snoop.assert_called_with(0x1000)

        # Assert state transition: INVALID -> EXCLUSIVE
        self.assertEqual(next_state, MESIState.EXCLUSIVE)


    def test_processor_read_invalid_and_hit(self):
        """
        Test handling a processor read request for a cacheline in INVALID state and HIT snoop result
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.HIT

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.INVALID, address, is_processor_write=False)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.READ, 0x1000)

        # Check that the snoop result was checked
        self.mock_get_snoop.assert_called_with(0x1000)

        # Assert state transition: INVALID -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)

    def test_processor_read_invalid_and_hitm(self):
        """
        Test handling a processor read request for a cacheline in INVALID state and HITM snoop result
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.HITM

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.INVALID, address, is_processor_write=False)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.READ, 0x1000)

        # Check that the snoop result was checked
        self.mock_get_snoop.assert_called_with(0x1000)

        # Assert state transition: INVALID -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)


    def test_processor_write_invalid_and_nohit(self):
        """
        Test handling a processor write request for a cacheline in INVALID state and NOHIT snoop result
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.NOHIT

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.INVALID, address, is_processor_write=True)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.RWIM, 0x1000)

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: INVALID -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)

    def test_processor_write_invalid_and_hit(self):
        """
        Test handling a processor write request for a cacheline in INVALID state and HIT snoop result
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.HIT

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.INVALID, address, is_processor_write=True)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.RWIM, 0x1000)

        # Check that the snop result was checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: INVALID -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)


    def test_processor_read_shared(self):
        """
        Test handling a processor read request for a cacheline in SHARED state
        """
        address = 0x1000
        self.mock_get_snoop.return_value = SnoopResult.HIT

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.SHARED, address, is_processor_write=False)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_not_called()

        # Check that the snoop result was checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: SHARED -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)

    def test_processor_write_shared(self):
        """
        Test handling a processor write request for a cacheline in SHARED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.SHARED, address, is_processor_write=True)

        # Check that the bus operation was called with the correct arguments
        self.mock_bus_op.assert_called_with(BusOp.INVALIDATE, 0x1000)

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: SHARED -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)

    def test_processor_read_exclusive(self):
        """
        Test handling a processor read request for a cacheline in EXCLUSIVE state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.EXCLUSIVE, address, is_processor_write=False)

        # Check that the bus operation was not called
        self.mock_bus_op.assert_not_called()

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: EXCLUSIVE -> EXCLUSIVE
        self.assertEqual(next_state, MESIState.EXCLUSIVE)

    def test_processor_write_exclusive(self):
        """
        Test handling a processor write request for a cacheline in EXCLUSIVE state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.EXCLUSIVE, address, is_processor_write=True)

        # Check that the bus operation was not called, silent upgrade
        self.mock_bus_op.assert_not_called()

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: EXCLUSIVE -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)

    def test_processor_write_modified(self):
        """
        Test handling a processor write request for a cacheline in MODIFIED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.MODIFIED, address, is_processor_write=True)

        # Check that the bus operation was not called
        self.mock_bus_op.assert_not_called()

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: MODIFIED -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)

    def test_processor_read_modified(self):
        """
        Test handling a processor read request for a cacheline in MODIFIED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_processor_request(MESIState.MODIFIED, address, is_processor_write=False)

        # Check that the bus operation was not called
        self.mock_bus_op.assert_not_called()

        # Check that the snoop result was not checked
        self.mock_get_snoop.assert_not_called()

        # Assert state transition: MODIFIED -> MODIFIED
        self.assertEqual(next_state, MESIState.MODIFIED)

    ############################################################################################################
    # Snoop tests

    def test_snoop_invalid_bus_read(self):
        """
        Test handling a snooped bus read operation for a cacheline in INVALID state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.INVALID, BusOp.READ, address)

        # Check that the snoop result was put
        self.mock_put_snoop.assert_called_with(address, SnoopResult.NOHIT)

        # Assert state transition: INVALID -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_invalid_bus_write(self):
        """
        Test handling a snooped bus write operation for a cacheline in INVALID state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.INVALID, BusOp.WRITE, address)

        # Check that the snoop result was not put
        self.mock_put_snoop.assert_called_with(address, SnoopResult.NOHIT)

        # Assert state transition: INVALID -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_invalid_bus_rwim(self):
        """
        Test handling a snooped bus RWIM operation for a cacheline in INVALID state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.INVALID, BusOp.RWIM, address)

        # Check that the snoop result was not put
        self.mock_put_snoop.assert_called_with(address, SnoopResult.NOHIT)

        # Assert state transition: INVALID -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_invalid_bus_invalidate(self):
        """
        Test handling a snooped bus invalidate operation for a cacheline in INVALID state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.INVALID, BusOp.INVALIDATE, address)

        # Check that the snoop result was not put
        self.mock_put_snoop.assert_called_with(address, SnoopResult.NOHIT)

        # Assert state transition: INVALID -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_shared_bus_read(self):
        """
        Test handling a snooped bus read operation for a cacheline in SHARED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.SHARED, BusOp.READ, address)

        # Check that the snoop result was not put
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Assert state transition: SHARED -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)

    def test_snoop_shared_bus_write(self):
        """
        Test handling a snooped bus write operation for a cacheline in SHARED state, 
        this would never happpen under MESI protocol but might happen in a trace file.
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.SHARED, BusOp.WRITE, address)

        # Check that the snoop result was not put
        self.mock_put_snoop.assert_not_called()

        # Check that the L1 cache was sent invalidate message
        self.mock_l1_message.assert_not_called()

        # Assert state transition: SHARED -> INVALID
        # TODO: Not sure if this is how we'd want to handle this corner case
        self.assertEqual(next_state, MESIState.SHARED)

    def test_snoop_shared_bus_rwim(self):
        """
        Test handling a snooped bus RWIM operation for a cacheline in SHARED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.SHARED, BusOp.RWIM, address)

        # Check that the snoop result was called with HIT
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Check that the L1 cache was sent invalidate message
        self.mock_l1_message.assert_called_with(CacheMessage.INVALIDATELINE, address)

        # Assert state transition: SHARED -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_shared_bus_invalidate(self):
        """
        Test handling a snooped bus invalidate operation for a cacheline in SHARED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.SHARED, BusOp.INVALIDATE, address)

        # Check that the snoop result was called with HIT
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Check that the L1 cache was sent invalidate message
        self.mock_l1_message.assert_called_with(CacheMessage.INVALIDATELINE, address)

        # Assert state transition: SHARED -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)


    def test_snoop_modified_bus_read(self):
        """
        Test handling a snooped bus read operation for a cacheline in MODIFIED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.MODIFIED, BusOp.READ, address)

        # Check that the snoop result was put with HITM
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HITM)

        # Check that the L1 cache was sent get line message
        self.mock_l1_message.assert_called_with(CacheMessage.GETLINE, address)

        # Check that bus operation was called with WRITE
        self.mock_bus_op.assert_called_with(BusOp.WRITE, address)

        # Assert state transition: MODIFIED -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)

    def test_snoop_modified_bus_rwim(self):
        """
        Test handling a snooped bus RWIM operation for a cacheline in MODIFIED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.MODIFIED, BusOp.RWIM, address)

        # Check that the snoop result was put with HITM
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HITM)

        # Check that bus operation was called with WRITE
        self.mock_bus_op.assert_called_with(BusOp.WRITE, address)

        # In sequence of calls, first get line and then invalidate
        expected_l1_calls = [
            unittest.mock.call(CacheMessage.GETLINE, address),
            unittest.mock.call(CacheMessage.INVALIDATELINE, address)
        ]

        # Check that the L1 cache was sent getline and invalidate messages
        self.mock_l1_message.assert_has_calls(expected_l1_calls, any_order=False)

        # Assert state transition: MODIFIED -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_modified_bus_invalidate(self):
        """
        Test handling a snooped bus invalidate operation for a cacheline in MODIFIED state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.MODIFIED, BusOp.INVALIDATE, address)

        # Check that the snoop result was put with HITM
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HITM)

        # Check that bus operation was called with WRITE
        self.mock_bus_op.assert_called_with(BusOp.WRITE, address)

        # In sequence of calls, first get line and then invalidate
        expected_l1_calls = [
            unittest.mock.call(CacheMessage.GETLINE, address),
            unittest.mock.call(CacheMessage.INVALIDATELINE, address)
        ]

        # Check that the L1 cache was sent getline and invalidate messages
        self.mock_l1_message.assert_has_calls(expected_l1_calls, any_order=False)

        # Assert state transition: MODIFIED -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_modified_bus_write(self):
        """
        Test handling a snooped bus write operation for a cacheline in MODIFIED state
        Note: This would never happen under MESI protocol, but test if for completeness 
        of all cases. Although it would happen under MESI protocol, the trace file may generate 
        this scenario
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.MODIFIED, BusOp.WRITE, address)

        # Assert state transition: MODIFIED -> MODIFIED
        # TODO: Not sure if this is how we'd want to handle this corner case
        self.assertEqual(next_state, MESIState.MODIFIED)

    def test_snoop_exclusive_bus_read(self):
        """
        Test handling a snooped bus read operation for a cacheline in EXCLUSIVE state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.EXCLUSIVE, BusOp.READ, address)

        # Check that the snoop result was put with HIT
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Assert state transition: EXCLUSIVE -> SHARED
        self.assertEqual(next_state, MESIState.SHARED)

    def test_snoop_exclusive_bus_rwim(self):
        """
        Test handling a snooped bus RWIM operation for a cacheline in EXCLUSIVE state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.EXCLUSIVE, BusOp.RWIM, address)

        # Check that the snoop result was put with HIT
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Check that the L1 cache was sent invalidate message
        self.mock_l1_message.assert_called_with(CacheMessage.INVALIDATELINE, address)

        # Assert state transition: EXCLUSIVE -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)

    def test_snoop_exclusive_bus_invalidate(self):
        """
        Test handling a snooped bus invalidate operation for a cacheline in EXCLUSIVE state
        """
        address = 0x1000

        # Call the function under test
        next_state = self.controller.handle_snoop(MESIState.EXCLUSIVE, BusOp.INVALIDATE, address)

        # Check that the snoop result was put with HIT
        self.mock_put_snoop.assert_called_with(address, SnoopResult.HIT)

        # Check that the L1 cache was sent invalidate message
        self.mock_l1_message.assert_called_with(CacheMessage.INVALIDATELINE, address)

        # Assert state transition: EXCLUSIVE -> INVALID
        self.assertEqual(next_state, MESIState.INVALID)
  
if __name__ == '__main__':
    unittest.main()