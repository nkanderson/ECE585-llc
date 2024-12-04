def generate_files() -> None:
    """
    Generate large files to test our cache simulation program with.
    These files will not be checked in to the repo, because they are
    too large, and there is no need if they are dynamically created
    in a reasonable amount of time.

    Generates the following:
    - large_read.txt: Read events for one sixteenth of all addresses
      Should result in 2^23 read events, and 2^23 cache misses,
      no writes, no hits.
      Contains 8388608 lines.
    - large_read_write.txt: Read events for 1 Mi addresses, then
      read and write half of them again.
      Should result in 1.5 Mi read events, 2^20 misses, 2^10 hits, 512 Ki writes;
      50% hit rate.
      Contains 2097152 lines.
    """
    with open("src/data/large_read.txt", "w") as f:
        # Go through all possible addresses, stepping by 512 bytes
        # to target a new cache set and line with each request
        for i in range(0, 2**32, 512):
            # Format second column as hexadecimal with no leading '0x'
            hex_value = hex(i).lstrip("0x") or "0"
            f.write(f"0 {hex_value}\n")

    with open("src/data/large_read_write.txt", "w") as f:
        # Go through all possible addresses, stepping by 2^12 bytes
        # to target a new cache set and line with each request
        step = 1 << 12
        for i in range(0, 2**32, step):
            # Format second column as hexadecimal with no leading '0x'
            hex_value = hex(i).lstrip("0x") or "0"
            f.write(f"0 {hex_value}\n")
            # Every other iteration, add another read and write
            if (i // step) % 2 == 0:
                f.write(f"1 {hex_value}\n")
                f.write(f"0 {hex_value}\n")


def main():
    generate_files()


if __name__ == "__main__":
    main()
