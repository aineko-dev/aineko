# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Functions for validation checks used in pydantic models."""

import re


def check_power_of_2(x: int) -> int:
    """Check if the given integer is a power of 2.

    Args:
        x: integer to check

    Returns:
        The input integer if it is a power of 2.

    Raises:
        ValueError: if the input integer is not a power of 2.
    """
    if not ((x & (x - 1) == 0) and x != 0):
        raise ValueError("Value must be a power of 2")
    return x


def check_semver(x: str) -> str:
    """Check if the given string is a semantic version.

    Regex taken from:
    https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string

    Args:
        x: string to check

    Returns:
        The input string if it is a semantic version.

    Raises:
        ValueError: if the input string is not a semantic version.
    """
    regex = (
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))"
        r"?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )
    if re.search(regex, x) is None:
        raise ValueError("Version must be in the form `1.2.3`")
    return x
