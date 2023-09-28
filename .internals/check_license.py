# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
import argparse
import sys
from typing import List, Optional

LICENSE_SNIPPET = """# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""


def check_license(filename: str) -> bool:
    """Check that the correct license snippet is present in the file.

    Args:
        filename: The file to check.

    Returns:
        True if the license snippet is present and correct, False otherwise.
    """
    with open(filename, "r") as f:
        lines = [f.readline().strip() for _ in range(2)]
        return "\n".join(lines) == LICENSE_SNIPPET.strip()


def fix_license(filename: str) -> None:
    """Add the correct license snippet to the file.

    Args:
        filename: The file to fix.
    """
    if not check_license(filename):
        try:
            print(f"Fixing license in {filename}")
            with open(filename, "r+") as file:
                content = file.read()
                file.seek(0, 0)
                file.write(LICENSE_SNIPPET + content)
        except Exception as e:
            print(f"ERROR: Could not fix license in {filename}: {e}")


def main() -> None:
    """Main entrypoint for the check_license script."""
    parser = argparse.ArgumentParser(
        description="Check and fix license headers in files."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix the file by adding the license snippet.",
    )
    parser.add_argument(
        "filenames", nargs="+", help="The files to check or fix."
    )
    args = parser.parse_args()
    for filename in args.filenames:
        if args.fix:
            fix_license(filename)
        else:
            if not check_license(filename):
                print(
                    f"ERROR: License snippet missing or incorrect in {filename}"
                )
                sys.exit(1)


if __name__ == "__main__":
    main()
