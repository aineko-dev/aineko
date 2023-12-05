# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests of miscellaneous utility functions."""
from aineko.utils.misc import truthy


def test_truthy():
    """Test for truthy value checker."""
    assert truthy("True")
    assert truthy("TRUE")
    assert truthy("tRuE")
    assert truthy(1)
    assert truthy("1")
    assert truthy(True)
