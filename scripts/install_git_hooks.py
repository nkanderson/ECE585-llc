#!/usr/bin/env python3

import os
import shutil
import stat

# Define the source and destination directories
SOURCE_HOOKS_DIR = "scripts/hooks"
DEST_HOOKS_DIR = ".git/hooks"


def main():
    # Check if the .git directory exists
    if not os.path.isdir(".git"):
        print(
            "Error: .git directory not found. Please run this script from the root of a Git repository."
        )
        return

    # Check if the destination hooks directory exists
    if not os.path.isdir(DEST_HOOKS_DIR):
        print("Error: .git/hooks directory not found.")
        return

    # Copy each hook from scripts/hooks to .git/hooks
    print("Installing Git hooks...")
    for hook_name in os.listdir(SOURCE_HOOKS_DIR):
        source_hook_path = os.path.join(SOURCE_HOOKS_DIR, hook_name)
        dest_hook_path = os.path.join(DEST_HOOKS_DIR, hook_name)

        # Only copy if it's a file
        if os.path.isfile(source_hook_path):
            shutil.copy(source_hook_path, dest_hook_path)

            # Make the destination file executable
            st = os.stat(dest_hook_path)
            os.chmod(dest_hook_path, st.st_mode | stat.S_IEXEC)

            print(f"Installed {hook_name}")
        else:
            print(f"Skipping {hook_name} (not a file)")

    print("Git hooks installed successfully.")


if __name__ == "__main__":
    main()
