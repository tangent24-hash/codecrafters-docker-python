import os
import subprocess
import tempfile
import sys

def main():
    # Remove the print statement for debugging
    # print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    command = sys.argv[3]
    args = sys.argv[4:]

    # Create a temporary directory for chroot
    with tempfile.TemporaryDirectory() as tempdir:
        # Copy the binary to the temporary directory (assuming it's available)
        try:
            subprocess.run(["cp", command, tempdir], check=True)
        except FileNotFoundError:
            print(f"Error: Could not find binary {command}")
            sys.exit(1)

        # Change root to the temporary directory
        os.chroot(tempdir)

        # Execute the command with the copied binary path
        completed_process = subprocess.run(
            ["./"+command, *args], capture_output=True, check=False)

        # Print both stdout and stderr (decode from bytes)
        sys.stderr.write(completed_process.stderr.decode("utf-8"))
        sys.stdout.write(completed_process.stdout.decode("utf-8"))

        # Exit with the same code as the child process
        sys.exit(completed_process.returncode)


if __name__ == "__main__":
    main()
