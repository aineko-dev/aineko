"""Node code for Node Manager.

The Node Manager is a special node that exists in every
pipeline and is responsible for the following tasks:
 - Killing all other nodes
"""

from typing import Optional
from aineko.core.node import AbstractNode

class NodeManager(AbstractNode):
    """Manages all other nodes in pipeline."""

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """State contains all other actor handles.
        
        params: mapping of node name to node actor handles
        """
        self.nodes = params["actors"]

    def _execute(self, params: Optional[dict] = None) -> None:
        """Kills all other nodes."""
        for node in self.nodes:
            node.kill()