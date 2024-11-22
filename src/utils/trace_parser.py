import sys
from pathlib import Path
from typing import Optional, Tuple

from common.constants import TraceCommand
from config.project_config import DATA_DIRECTORY, DEFAULT_TRACE_FILE, ROOT_DIR, config


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

    def __init__(self, filename: Optional[str] = None):
        """
        Initialize the parser with an optional filename.

        Args:
            filename (Optional[str]): Path to the trace file. If None, uses default.
        """
        self.fd = None
        if filename is None:
            print(
                f"[INFO] - Using default file: {ROOT_DIR/DATA_DIRECTORY/DEFAULT_TRACE_FILE}"
            )
            self.filename = str(
                ROOT_DIR / DATA_DIRECTORY / DEFAULT_TRACE_FILE
            )  # Default as specified in project_config
        else:
            self.filename = self._validate_file_path(filename)

    @staticmethod
    def _validate_file_path(filepath: str) -> str:
        """
        Validate and normalize the provided file path.

        Raises:
            ValueError: If the file path is invalid or file doesn't exist

        """
        try:
            path = Path(filepath).resolve()  # Resolves symlinks and makes path absolute
            if not path.is_file():
                raise ValueError(f"File does not exist: {filepath}")
            return str(path)
        except Exception as e:
            raise ValueError(f"Invalid file path: {filepath}") from e

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
        Read and parse a single line from the trace file.

        Returns:
            Optional[Tuple[TraceCommand, Optional[int]]]: A tuple containing:
                - TraceCommand: The type of cache operation
                - int: The memory address in hexadecimal
                Returns None if EOF is reached or if line is invalid.

        Notes:
            - Skips empty lines
            - Recursively calls itself on invalid lines
            - Each line should contain an operation code and hex address
        """
        line = self.fd.readline()
        if not line:  # EOF, detects if line == ""
            self.close()
            print("[INFO] : Trace Read Complete")
            return None

        # Strip leading and trailing whitespace, and remove newline character
        line = line.strip()
        if not line:
            # Blank line detected, go to next line
            return self.read_line()

        try:
            # Split fields ->> [Operation] [Address]
            parts = line.split()
            if len(parts) < 2:
                print(
                    "[WARNING] : Invalid line read from trace, recursing to next line"
                )
                return self.read_line()

            op = TraceCommand(int(parts[0]))  # Cast to enum class
            addr = int(
                parts[1], 16
            )  # Convert string to integer using base 16 (i.e. hex)
            return op, addr

        except ValueError:
            print(f"[WARNING] : Invalid line format : {line.strip()}")
            return self.read_line()
        except Exception as e:
            print(f"[ERROR] : Couldn't parse line: {e}")
            return self.read_line()

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


# Small test for parser
def main():
    """Main entry point for the trace file parser utility"""
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
                    print(f"Operation: {op.value} {op.name:20} Address: 0x{addr:08x}")
    except ValueError as e:
        print(f"[ERROR] - {str(e)}")
        return 1
    except Exception as e:
        print(f"[ERROR] - An unexpected error occurred: {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
