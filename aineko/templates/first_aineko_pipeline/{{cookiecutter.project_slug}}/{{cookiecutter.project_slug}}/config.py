# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Example file setting default configs for project."""

from aineko.config import BaseConfig


# pylint: disable=invalid-name
class DEFAULT_CONFIG(BaseConfig):
    """Default configs for project."""

    NUM_CPUS = 0.5
