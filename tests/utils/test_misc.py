# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for misc utils."""

from aineko.utils.misc import truthy


def test_truthy():
    """Test that truthy returns True for truthy values."""
    assert truthy("true")
    assert truthy("True")
    assert truthy("TRUE")
    assert truthy("1")
    assert truthy(1)
    assert truthy(True)
