#!/usr/bin/env python3
"""Check Railway collector status."""

import subprocess
import sys


def main():
    result = subprocess.run(
        ["railway", "deployment", "list", "--service", "OrbitMind"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Status: Unknown (Railway CLI error)")
        sys.exit(1)

    lines = result.stdout.strip().split("\n")

    # Find latest deployment (first non-header line)
    for line in lines[1:]:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                status = parts[1]
                if status in ("SUCCESS", "RUNNING"):
                    print("Status: Collecting")
                elif status == "REMOVED":
                    print("Status: Stopped")
                elif status == "BUILDING":
                    print("Status: Starting...")
                elif status == "FAILED":
                    print("Status: Failed")
                else:
                    print(f"Status: {status}")
                return

    print("Status: No deployments found")


if __name__ == "__main__":
    main()
