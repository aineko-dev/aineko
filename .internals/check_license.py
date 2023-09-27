# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
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


def main(argv: Optional[List[str]] = None) -> None:
    """Main entrypoint for the check_license script."""
    if argv is None:
        argv = sys.argv[1:]

    for filename in argv:
        if not filename.endswith(".py"):
            continue
        if not check_license(filename):
            print(f"ERROR: License snippet missing or incorrect in {filename}")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
