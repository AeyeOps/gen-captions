#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from dotenv import dotenv_values

# Define temp file
TEMP_ENV = ".env.aider.consolidated.tmp"


def merge_env_files():
    # Define the order of env files
    env_files = [".env", ".env.aider", ".env.aider.local", ".env.local"]

    # Merge all environment variables
    consolidated_env = {}
    for env_file in env_files:
        if Path(env_file).exists():
            consolidated_env.update(dotenv_values(dotenv_path=env_file))

    return consolidated_env


def write_temp_env(env_vars):
    # Write consolidated environment to temp file
    with open(TEMP_ENV, "w") as f:
        for key, value in env_vars.items():
            if value is not None:  # Skip None values
                f.write(f"{key}={value}\n")


def main():
    try:
        # Clean up existing temp file
        if Path(TEMP_ENV).exists():
            print("Deleting existing temp file...")
            Path(TEMP_ENV).unlink()

        # Merge and write environment files
        print("Consolidating environment files into one temp file...")
        consolidated_env = merge_env_files()
        print(f"Writing consolidated environment to temp file {TEMP_ENV}...")
        write_temp_env(consolidated_env)

        # Launch aider with the temp file
        print("Launching aider...")
        result = subprocess.run(
            ["aider", "--env", TEMP_ENV]
        )

        # Clean up
        print("Deleting temp file...")
        if Path(TEMP_ENV).exists():
            Path(TEMP_ENV).unlink()

        # Exit with aider's exit code
        print("Exiting with Aider's exit code...")
        sys.exit(result.returncode)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if Path(TEMP_ENV).exists():
            Path(TEMP_ENV).unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()
