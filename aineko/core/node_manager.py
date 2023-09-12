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

    def __init__(
        self, poison_pill: ray.actor.ActorHandle, test: bool = False
    ) -> None:
        """Initialize dict of actor handles."""
        super().__init__(poison_pill, test)
        self.actors = {}

    def _execute(self, params: Optional[dict] = None) -> None:
        """Kills all other nodes."""
        # Sleep to prevent high CPU usage
        time.sleep(0.1)
        # Explicitly accept True to prevent accidents
        if ray.get(self.poison_pill.get_state.remote()) is True:
            self.log("Poison pill activated, killing all nodes.")
            ray.shutdown()

    def add_actor(
        self, actor_name: str, actor_handle: ray.actor.ActorHandle
    ) -> None:
        """Add actor to actors attribute."""
        self.actors[actor_name] = actor_handle
