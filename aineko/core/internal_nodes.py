"""Internal nodes meant for system use."""
import time
from typing import Optional

import ray

from aineko.config import AINEKO_CONFIG, LOCAL_KAFKA_CONFIG
from aineko.core.node import AbstractNode


@ray.remote(num_cpus=AINEKO_CONFIG.get("DEFAULT_NUM_CPUS"))
class NodeManager(AbstractNode):
    """Node that manages other nodes in the pipelines.

    Functionalities include killing other nodes when test run is complete.

    Args:
        nodes (list): List of nodes in the pipeline to manage
        test_mode (bool): Whether the pipeline is running in test mode

    Attributes:
        nodes (list): List of nodes in the pipeline to manage
        test_mode (bool): Whether the pipeline is running in test mode
    """

    def __init__(self, nodes: Optional[list] = None, test_mode: bool = False):
        """Initializes the node manager.

        Args:
            nodes: List of nodes in the pipeline to manage
            test_mode: Whether the pipeline is running in test mode
        """
        super().__init__()
        self.nodes = nodes or []
        self.test_mode = test_mode

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Pre loop hook.

        Args:
            params: Parameters for the node
        """
        self.log("Node manager started", level="info")
        self.start_time = time.time()

    def kill_nodes(self, how: str = "all") -> None:
        """Kills all nodes.

        Args:
            how: How to kill the nodes. Only "all" is supported for now.

        Raises:
            NotImplementedError: If how is not supported.
        """
        if how == "all":
            for node in self.nodes:
                ray.kill(node)
        else:
            raise NotImplementedError("Only 'all' is supported for now")

    def manage_pipeline_test(self, timeout: int = 30) -> Optional[bool]:
        """Manages the pipeline in test mode.

        Args:
            timeout: Timeout in seconds after which to kill nodes

        Returns:
            False if nodes are killed else True
        """
        # Timeout
        if time.time() - self.start_time > timeout:
            self.log("Timeout reached, killing nodes", "critical")
            self.report("Killing all nodes: timeout")
            self.kill_nodes()
            return False

        # If kill message is received, kill all nodes
        message = self.consumers[
            LOCAL_KAFKA_CONFIG.get("REPORTING_DATASET")
        ].consume()
        if message is None:
            return None
        self.log(f"Received message: {message}", "info")
        if message["message"] == "Checker node completed successfully":
            self.log("Kill switch triggered, killing nodes", "critical")
            self.report("Killing all nodes: kill switch triggered")
            self.kill_nodes()
            return False

        return None

    # pylint: disable=unused-argument
    def _execute(self, params: Optional[dict] = None) -> None:
        """Execute main loop for node.

        Args:
            params: Parameters for the node
        """
        if self.test_mode:
            self.manage_pipeline_test()
