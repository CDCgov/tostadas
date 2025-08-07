#!/usr/bin/env python3
import time
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: wait_utility.py <seconds>", file=sys.stderr)
        sys.exit(1)
    
    try:
        wait_time = int(sys.argv[1])
        if wait_time < 0:
            raise ValueError("Wait time must be non-negative")
        time.sleep(wait_time)
    except ValueError as e:
        print(f"Error: Invalid wait time - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()