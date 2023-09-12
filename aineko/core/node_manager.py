"""Node code for Node Manager.

The Node Manager is a special node that exists in every
pipeline and is responsible for the following tasks:
 - Killing all other nodes
"""

from typing import Optional
import ray
import time
from aineko.core.node import AbstractNode

class NodeManager(AbstractNode):
    """Manages all other nodes in pipeline."""

    def __init__(self, poison_pill: ray.actor.ActorHandle, test: bool = False) -> None:
        """Initialize dict of actor handles."""
        super().__init__(poison_pill, test)
        self.actors = {}

    def _execute(self, params: Optional[dict] = None) -> None:
        """Kills all other nodes."""
        # Sleep to prevent high CPU usage
        time.sleep(1)
        # Explicitly accept True to prevent accidents
        if ray.get(self.poison_pill.get_state.remote()) is True:
            print("Killing nodes")
            self.kill_all_nodes()

    def add_actor(self, actor_name: str, actor_handle: ray.actor.ActorHandle) -> None:
        """Add actor to actors attribute."""
        self.actors[actor_name] = actor_handle

    def kill_all_nodes(self):
        """Poison pill method to kill all nodes in pipeline."""
        for node_name, node in self.actors.items():
            ray.kill(node)
            self.log(f"Killed node {node_name}", level="critical")
            print(f"Killed node {node_name}")
            self.actors.pop(node_name)
        ray.shutdown()
