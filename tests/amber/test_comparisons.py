# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test Amber comparisons module."""
from aineko.amber.comparisons import greater_than


# pylint: disable=no-member
def test_greater_than():
    """Test greater_than method."""

    trials = [
        (1, {"threshold": 2}, False),
        (2, {"threshold": 1}, True),
        (1, {"threshold": 1}, False),
        (1, {"threshold": "2"}, False),
        (1, {"threshold": "1"}, False),
    ]
    for value, params, expected in trials:
        assert greater_than(value, params) == expected
