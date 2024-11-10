import unittest
from io import StringIO

from common.constants import BusOp, CacheMessage, LogLevel, SnoopResult
from utils.cache_logger import CacheLogger, log_operation


class TestCacheLogger(unittest.TestCase):
    def setUp(self):
        # Create string buffers to capture output
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.logger = CacheLogger(
            level=LogLevel.DEBUG, stdout=self.stdout, stderr=self.stderr
        )

    def tearDown(self):
        self.stdout.close()
        self.stderr.close()

    def create_dummy_cache_with_logger(self, logger):
        class DummyCache:
            @log_operation(logger=logger)  # Will be set in tests
            def BusOperation(
                self, bus_op: int, address: int, snoop_result: int
            ) -> None:
                return None

            @log_operation(logger=logger)
            def GetSnoopResult(self, address: int) -> int:
                return SnoopResult.HIT

            @log_operation(logger=logger)
            def PutSnoopResult(self, address: int, snoop_result: int) -> None:
                return None

            @log_operation(logger=logger)
            def MessageToCache(self, message: int, address: int) -> None:
                return None

        return DummyCache()

    def test_logging_levels(self):
        """Test that different logging levels work correctly"""
        # Test SILENT level
        silent_logger = CacheLogger(
            level=LogLevel.SILENT, stdout=StringIO(), stderr=StringIO()
        )
        silent_logger.log(LogLevel.SILENT, "Silent message")
        silent_logger.log(LogLevel.NORMAL, "Normal message")
        silent_logger.log(LogLevel.DEBUG, "Debug message")

        self.assertIn("Silent message", silent_logger.stdout.getvalue())
        self.assertEqual("", silent_logger.stderr.getvalue())

        # Test NORMAL level
        normal_logger = CacheLogger(
            level=LogLevel.NORMAL, stdout=StringIO(), stderr=StringIO()
        )
        normal_logger.log(LogLevel.SILENT, "Silent message")
        normal_logger.log(LogLevel.NORMAL, "Normal message")
        normal_logger.log(LogLevel.DEBUG, "Debug message")

        self.assertIn("Silent message", normal_logger.stdout.getvalue())
        self.assertIn("Normal message", normal_logger.stderr.getvalue())
        self.assertNotIn("Debug message", normal_logger.stderr.getvalue())

    def test_bus_operation_logging(self):
        """Test logging of bus operations"""
        dummy = self.create_dummy_cache_with_logger(self.logger)

        # Test bus operation
        dummy.BusOperation(BusOp.READ, 0x1234, SnoopResult.NOHIT)

        stderr_output = self.stderr.getvalue()
        self.assertIn("BusOp: READ", stderr_output)
        self.assertIn("Address: 1234", stderr_output)
        self.assertIn("Snoop Result: NOHIT", stderr_output)

    def test_snoop_result_logging(self):
        """Test logging of snoop results"""
        dummy = self.create_dummy_cache_with_logger(self.logger)

        # Test get snoop result
        dummy.GetSnoopResult(0x5678)
        stderr_output = self.stderr.getvalue()
        self.assertIn("GetSnoopResult: Address 5678", stderr_output)
        self.assertIn("Snoop Result: HIT", stderr_output)

        # Clear buffer
        self.stderr.seek(0)
        self.stderr.truncate()

        # Test put snoop result
        dummy.PutSnoopResult(0x9ABC, SnoopResult.NOHIT)
        stderr_output = self.stderr.getvalue()
        self.assertIn("SnoopResult: Address 9abc", stderr_output)
        self.assertIn("SnoopResult: NOHIT", stderr_output)

    def test_message_to_cache_logging(self):
        """Test logging of cache messages"""
        dummy = self.create_dummy_cache_with_logger(self.logger)

        dummy.MessageToCache(CacheMessage.INVALIDATELINE, 0xDEF0)
        stderr_output = self.stderr.getvalue()
        self.assertIn("L2: INVALIDATELINE def0", stderr_output)

    def test_logger_output_demonstration(self):
        """Demonstration test that shows actual logger output"""
        # Create a logger that writes to both StringIO (for assertions) and console
        import sys

        demo_logger = CacheLogger(
            level=LogLevel.DEBUG,
            stdout=sys.stdout,  # Write to console
            stderr=sys.stderr,  # Write to console
        )

        print("\n=== Logger Output Demonstration ===")
        print("This test shows actual logger output at different levels:\n")

        # Create dummy cache with this logger
        dummy = self.create_dummy_cache_with_logger(demo_logger)

        print("1. Testing Bus Operation logging:")
        dummy.BusOperation(BusOp.READ, 0x1234, SnoopResult.NOHIT)

        print("\n2. Testing Snoop Result logging:")
        dummy.GetSnoopResult(0x5678)
        dummy.PutSnoopResult(0x9ABC, SnoopResult.NOHIT)

        print("\n3. Testing Cache Message logging:")
        dummy.MessageToCache(CacheMessage.INVALIDATELINE, 0xDEF0)

        print("\n=== End Logger Output Demonstration ===")

    def test_file_logging(self):
        """Demonstration of logging to files. Creates debug.log and stats.log in the
        tests/utils directory."""
        import os

        # Get the directory where the test file is located
        test_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"\nCreating log files in: {test_dir}")

        # Specify files with full paths
        debug_path = os.path.join(test_dir, "debug.log")
        stats_path = os.path.join(test_dir, "stats.log")

        try:
            # Open files for writing
            with open(debug_path, "w") as debug_file, open(
                stats_path, "w"
            ) as stats_file:
                file_logger = CacheLogger(
                    level=LogLevel.DEBUG, stdout=stats_file, stderr=debug_file
                )

                # Create dummy cache with this logger
                dummy = self.create_dummy_cache_with_logger(file_logger)

                # Perform various operations
                dummy.BusOperation(BusOp.READ, 0x1234, SnoopResult.NOHIT)
                dummy.GetSnoopResult(0x5678)
                dummy.PutSnoopResult(0x9ABC, SnoopResult.NOHIT)
                dummy.MessageToCache(CacheMessage.INVALIDATELINE, 0xDEF0)

                # Ensure everything is written
                debug_file.flush()
                stats_file.flush()

            print("\nLog files have been created at:")
            print(f"Debug log: {debug_path}")
            print(f"Stats log: {stats_path}")

        except Exception as e:
            print(f"Error during file operations: {str(e)}")


if __name__ == "__main__":
    unittest.main()
