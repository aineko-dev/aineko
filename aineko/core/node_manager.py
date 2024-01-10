# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Node code for Node Manager.

The Node Manager is a special node that exists in every
pipeline and is responsible for the following tasks:
 - Killing the ray instance when the poison pill is activated
"""

import time
from typing import Optional

import ray

from aineko.core.node import AbstractNode


class NodeManager(AbstractNode):
    """Manages all other nodes in pipeline."""

    def _execute(self, params: Optional[dict] = None) -> None:
        """Kills all other nodes."""
        # Sleep to prevent high CPU usage
        time.sleep(0.1)
        if self.poison_pill:
            if ray.get(self.poison_pill.get_state.remote()):
                self.log("Poison pill activated, killing all nodes.")
                ray.shutdown()
