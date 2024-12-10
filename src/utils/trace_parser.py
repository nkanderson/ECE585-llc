import sys
import warnings
from pathlib import Path
from typing import Optional, Tuple

from common.constants import LogLevel, TraceCommand
from config.project_config import DATA_DIRECTORY, DEFAULT_TRACE_FILE, ROOT_DIR, config
from utils.cache_logger import CacheLogger


class TraceFileParser:
    """
    A parser for reading and processing cache simulation trace files.

    This class handles reading trace files that contain cache operations and addresses.
    It supports both default and user-specified trace files and implements context
    manager protocol for safe file handling.

    Attributes:
        filename (str): Path to the trace file
        fd: File descriptor for the opened trace file
    """

    def __init__(
        self,
        filename: Optional[str] = None,
        logger: Optional[CacheLogger] = None,
    ):
        """
        Initialize the parser with an optional filename.

        Args:
            filename (Optional[str]): Path to the trace file. If None, uses default.
        """
        self.logger = logger if logger is not None else config.get_logger()

        self.fd = None
        self.filename = self._get_valid_filepath(filename)
        self.logger.log(LogLevel.DEBUG, f"Using trace file: {self.filename}")

    @staticmethod
    def _get_valid_filepath(filepath: str) -> str:
        """
        Validate the provided file path or return the default file path.

        Args:
            filepath: Optional file path to validate

        Raises RuntimeWarning if the file path provided is invalid or the file does not exist.

        Returns:
            str: Valid file path (either provided path or default path)
        """
        if filepath is None:
            return str(ROOT_DIR / DATA_DIRECTORY / DEFAULT_TRACE_FILE)

        try:
            path = Path(filepath).resolve()
            if path.is_file():
                return str(path)
        except Exception:
            pass

        warnings.warn(f"Invalid file path: {filepath}. Using default trace file.")
        return str(ROOT_DIR / DATA_DIRECTORY / DEFAULT_TRACE_FILE)

    def open(self) -> bool:
        """Open the trace file"""
        try:
            self.fd = open(self.filename, "r", encoding="utf-8")
            return True
        except FileNotFoundError:
            print(f"[ERROR] - could not find trace file '{self.filename}'")
            return False
        except PermissionError:
            print(f"[ERROR] - Permission denied accessing file: '{self.filename}'")
            return False
        except Exception as e:
            print(f"[ERROR] - Opening file: {e}")
            return False

    def close(self):
        """Close the trace file"""
        if self.fd:
            try:
                self.fd.close()
            except Exception as e:
                print(f"[ERROR] - Closing file: {str(e)}")

    def read_line(self) -> Optional[Tuple[TraceCommand, Optional[int]]]:
        """
        Read and parse one line at a time from the trace file.
        """
        while True:
            line = self.fd.readline()
            if not line:  # EOF
                self.close()
                self.logger.log(
                    LogLevel.DEBUG, "[COMPLETE] - End of trace file reached."
                )
                return None

            result = self._parse_line(line)
            if result is not None:
                return result

    def read_in_chunks(self, chunk_size: int = 1024):
        """
        Generator that reads and parses the file in chunks of given size.

        Args:
            chunk_size (int): Size of each chunk in bytes.

        Yields:
            Tuple[TraceCommand, Optional[int]]: Parsed result from each valid line.
        """
        buffer = ""
        while True:
            chunk = self.fd.read(chunk_size)
            if not chunk:
                if buffer:
                    # Process any remaining line in the buffer
                    result = self._parse_line(buffer)
                    if result:  # Only yield valid results
                        yield result
                self.close()
                self.logger.log(
                    LogLevel.DEBUG, "[COMPLETE] - End of trace file reached."
                )
                return

            # NOTE: The buffer may contain a partial line at the end if the chunk
            # split a line in the middle
            buffer += chunk
            lines = buffer.splitlines(keepends=False)

            # Process all but the last line (it may be incomplete)
            for line in lines[:-1]:
                result = self._parse_line(line)
                if result:  # Skip invalid lines
                    yield result

            # Handle the last line separately depending on whether it is complete
            if chunk.endswith("\n"):
                # If the chunk ends with a newline, the last line is complete
                # or an EOF newline - either way, we should attempt to parse it
                result = self._parse_line(lines[-1])
                if result:
                    yield result
                buffer = ""  # Reset buffer since there's no partial line
            else:
                # Keep the last line in the buffer for the next chunk
                buffer = lines[-1]

    def _parse_line(self, line: str) -> Optional[Tuple[TraceCommand, Optional[int]]]:
        """
        Parse a single line from the trace file.

        Args:
            line (str): A single line from the trace file.

        Returns:
            Optional[Tuple[TraceCommand, Optional[int]]]: A tuple containing:
                - TraceCommand: The type of cache operation
                - int: The memory address in hexadecimal
            Returns None if the line is invalid.
        """
        # Strip leading and trailing whitespace, and remove newline character
        line = line.strip()
        if not line:
            return None  # Skip blank lines

        # Split fields ->> [Operation] [Address]
        parts = line.split()
        try:
            op = TraceCommand(int(parts[0]))  # Cast to enum class
        except (ValueError, IndexError):
            warnings.warn(f"Invalid line format: {line}")
            return None

        # Check that there aren't too many tokens in line
        if len(parts) > 2:
            warnings.warn(f"Invalid line format (too many tokens): {line}")
            return None

        # Handle commands without an address
        if op in (TraceCommand.CLEAR_CACHE, TraceCommand.PRINT_CACHE):
            return op, None

        # Ensure an address is present for other commands
        if len(parts) < 2:
            warnings.warn(f"Missing address for command {op.name} : {line}")
            return None

        try:
            # Convert string to integer using base 16 (i.e. hex)
            addr = int(parts[1], 16)
            return op, addr
        except ValueError:
            warnings.warn(f"Invalid address format: {line}")
            return None

    def __enter__(self):
        """Context manager for entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager for exit"""
        self.close()


"""
    ----------------END OF TraceFileParser Class----------------------------------------------------
    ------------------------------------------------------------------------------------------------
"""


def main():
    """
    Test program for the TraceFileParser class.

    Allows the TraceFileParser to be run directly as a script for testing
    and debugging purposes. Accepts command line arguments for debug mode
    and file selection.

    Example Usage:
        # From root directory
        > PYTHONPATH=./src python -m src.utils.trace_parser --debug
        # To specify a trace file
        > PYTHONPATH=./src python -m src.utils.trace_parser --debug --file src/data/rwims.din
    """
    config.initialize(sys.argv[1:])

    args = config.get_args()
    try:
        with TraceFileParser(args.file) as parser:
            while True:
                result = parser.read_line()
                if result is None:
                    break
                op, addr = result
                if args.debug:
                    print("[DEBUG] -Line read...")
                    # Format address differently based on whether it's None
                    addr_str = f"0x{addr:08x}" if addr is not None else "No Address"
                    print(f"Operation: {op.value} {op.name:20} Address: {addr_str}")
    except ValueError as e:
        print(f"[ERROR] - {str(e)}")
        return 1
    except Exception as e:
        print(f"[ERROR] - An unexpected error occurred: {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
