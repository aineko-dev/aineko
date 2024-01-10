# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Miscellaneous utilities."""


from typing import Union


def truthy(val: Union[str, int, bool]) -> bool:
    """Returns True if val is truthy, else False.

    Truthy values include:
        - "true" in any combination of capitalizations
        - "1"
        - 1
        - True
    Args:
        val: Value to check for truthiness.
    """
    return str(val).lower() in ["true", "1"]
