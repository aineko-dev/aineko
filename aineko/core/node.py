"""Node base class."""
import time
import traceback
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from aineko.config import DEFAULT_KAFKA_CONFIG, TESTING_NODE_CONFIG
from aineko.core.dataset import (
    DatasetConsumer,
    DatasetProducer,
    FakeDatasetConsumer,
    FakeDatasetProducer,
)


class AbstractNode(ABC):
    """Node base class for all nodes in the pipeline.

    Nodes are the building blocks of the pipeline and are responsible for
    executing the pipeline. Nodes are designed to be modular and can be
    combined to create a pipeline. The node base class provides helper methods
    for setting up the consumer and producer for a node. The execute method is
    a wrapper for the _execute method which is to be implemented by subclasses.
    The _execute method is where the node logic is implemented by the user.

    Attributes:
        consumers (dict): dict of DatasetConsumer objects for inputs to node
        producers (dict): dict of DatasetProducer objects for outputs of node
        last_hearbeat (float): timestamp of the last heartbeat
        test (bool): True if node is in test mode else False
        log_levels (tuple): tuple of log levels

    Methods:
        setup_datasets: setup the consumers and producers for a node
        execute: execute the node, wrapper for _execute method
        _execute: execute the node, to be implemented by subclasses
    """

    def __init__(self, test: bool = False) -> None:
        """Initialize the node."""
        self.last_heartbeat = time.time()
        self.consumers: Dict = {}
        self.producers: Dict = {}
        self.params: Dict = {}
        self.test = test
        self.log_levels = ("info", "debug", "warning", "error", "critical")

    def enable_test_mode(self) -> None:
        """Enable test mode."""
        self.test = True

    def setup_datasets(
        self,
        catalog: Dict[str, dict],
        node: str,
        pipeline: str,
        project: str,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
    ) -> None:
        """Setup the consumer and producer for a node.

        Args:
            catalog: dataset catalog configuration
            node: name of the node
            pipeline: name of the pipeline
            project: name of the project
            inputs: list of dataset names for the inputs to the node
            outputs: list of dataset names for the outputs of the node
        """
        inputs = inputs or []
        self.consumers = {
            dataset_name: DatasetConsumer(
                dataset_name=dataset_name,
                node_name=node,
                dataset_config=catalog.get(dataset_name, {}),
                pipeline_name=pipeline,
            )
            for dataset_name in inputs
        }

        outputs = outputs or []
        self.producers = {
            dataset_name: DatasetProducer(
                dataset_name=dataset_name,
                node_name=node,
                dataset_config=catalog.get(dataset_name, {}),
                pipeline_name=pipeline,
                project_name=project,
            )
            for dataset_name in outputs
        }

    def setup_test(
        self,
        inputs: Optional[dict] = None,
        outputs: Optional[list] = None,
        params: Optional[dict] = None,
    ) -> None:
        """Setup the node for testing.

        Args:
            inputs: inputs to the node, format should be {"dataset": [1, 2, 3]}
            outputs: outputs of the node, format should be
                ["dataset_1", "dataset_2", ...]
            params: dictionary of parameters to make accessible to _execute

        Raises:
            RuntimeError: if node is not in test mode
        """
        if self.test is False:
            raise RuntimeError(
                "Node is not in test mode. "
                "Please initialize with `enable_test_mode()`."
            )

        inputs = inputs or {}
        self.consumers = {
            dataset_name: FakeDatasetConsumer(
                dataset_name=dataset_name,
                node_name=self.__class__.__name__,
                values=values,
            )
            for dataset_name, values in inputs.items()
        }
        outputs = outputs or []
        outputs.extend(TESTING_NODE_CONFIG.get("DATASETS"))
        self.producers = {
            dataset_name: FakeDatasetProducer(
                dataset_name=dataset_name,
                node_name=self.__class__.__name__,
            )
            for dataset_name in outputs
        }
        self.params = params or {}

    def log(self, message: str, level: str = "info") -> None:
        """Log a message to the logging dataset.

        Args:
            message: Message to log
            level: Logging level. Defaults to "info". Options are:
                "info", "debug", "warning", "error", "critical"
        Raises:
            ValueError: if invalid logging level is provided
        """
        if level not in self.log_levels:
            raise ValueError(
                f"Invalid logging level {level}. Valid options are: "
                f"{', '.join(self.log_levels)}"
            )
        out_msg = {"log": message, "level": level}
        self.producers[DEFAULT_KAFKA_CONFIG.get("LOGGING_DATASET")].produce(
            out_msg
        )

    def catch_exception(self) -> None:
        """Catch an exception and report it.

        Args:
            exc: Exception to catch
        """
        exc_info = traceback.format_exc()
        self.log(exc_info, level="error")

    def execute(self, params: Optional[dict] = None) -> None:
        """Execute the node.

        Wrapper for _execute method to be implemented by subclasses.

        Args:
            params: Parameters to use to execute the node. Defaults to None.
        """
        params = params or {}
        run_loop = True

        try:
            self._pre_loop_hook(params)
        except Exception:  # pylint: disable=broad-except
            self.catch_exception()
            raise

        while run_loop is not False:
            # Monitoring
            try:
                run_loop = self._execute(params)  # type: ignore
            except Exception:  # pylint: disable=broad-except
                self.catch_exception()
                raise

        self.log(f"Execution loop complete for node: {self.__class__.__name__}")
        self._post_loop_hook(params)

    @abstractmethod
    def _execute(self, params: dict) -> Optional[bool]:
        """Execute the node.

        Args:
            params: Parameters to use to execute the node.

        Note:
            Method to be implemented by subclasses

        Raises:
            NotImplementedError: if method is not implemented in subclass
        """
        raise NotImplementedError("_execute method not implemented")

    def run_test(self, runtime: Optional[int] = None) -> dict:
        """Execute the node in testing mode.

        Runs the steps in execute that involves the user defined methods.
        Includes pre_loop_hook, _execute, and post_loop_hook.

        Args:
            runtime: Number of seconds to run the execute loop for.

        Returns:
            dict: dataset names and values produced by the node.
        """
        if self.test is False:
            raise RuntimeError(
                "Node is not in test mode. "
                "Please initialize with `enable_test_mode()`."
            )
        run_loop = True
        start_time = time.time()

        self._pre_loop_hook(self.params)
        while run_loop is not False:
            run_loop = self._execute(self.params)  # type: ignore

            # Do not end loop if runtime not exceeded
            if runtime is not None:
                if time.time() - start_time < runtime:
                    continue

            # End loop if all consumers are empty
            if self.consumers and all(
                consumer.empty for consumer in self.consumers.values()
            ):
                run_loop = False

        self._post_loop_hook(self.params)

        return {
            dataset_name: producer.values
            for dataset_name, producer in self.producers.items()
        }

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Hook to be called before the node loop. User overrideable.

        Args:
            params: Parameters to use to execute the node.

        Note:
            Method (optional) to be implemented by subclasses.
        """
        pass

    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        """Hook to be called after the node loop. User overrideable.

        Args:
            params: Parameters to use to execute the node.

        Note:
            Method (optional) to be implemented by subclasses.
        """
        pass
