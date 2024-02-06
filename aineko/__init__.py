# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Package information for the Aineko package."""


__version__ = "0.3.1"
__author__ = "Convex Labs Engineering"

import logging

from aineko.core.config_loader import ConfigLoader
from aineko.core.dataset import (
    DatasetConsumer,
    DatasetProducer,
    FakeDatasetConsumer,
    FakeDatasetProducer,
)
from aineko.core.node import AbstractNode
from aineko.core.runner import Runner


def _setup_logging() -> None:
    """Setup logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)d - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


_setup_logging()
