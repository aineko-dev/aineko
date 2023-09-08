"""Pipeline metrics classes."""
import time
from datetime import datetime
from itertools import cycle
from typing import Optional, Union

import ray

from aineko.config import AINEKO_CONFIG
from aineko.core.node import AbstractNode


class Metrics(AbstractNode):
    """Metrics base class.

    Provides an interface for generating metrics from messages in
    in a dataset. Metrics are computed as a function of the messages
    in the input dataset and are published to the metrics dataset. To
    add a new metric, add a new method to the sub-class to compute
    the metric and add intial values for the metric in the pre-loop
    hook if needed.

    Sub-classes should be split by the class of metric being computed.
    For example, we implement a sub-class for computing metrics related
    to logging and a sub-class for computing metrics related to availability.

    Attributes:
        metrics (dict): Metrics
        last_produce (float): Time of last metric produced
        interval (int): Interval between metric production
        ignore_nodes (list): Nodes to ignore messages from
        ignore_pipelines (list): Pipelines to ignore messages from
        input_datasets (itertools.cycle): Cycle of input datasets

    Methods:
        _pre_loop_hook: called upon initialization.
        get_message: Get the next message from the list of input datasets.
        produce_metric: Produce a metric to the metrics dataset.
        seconds_since_produce: Get the seconds passed since the last metric
            was produced.
        validate_message: Validate a message.
        seconds_since_timestamp: Get the seconds passed since the message
            timestamp.
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Prepare metrics.

        Args:
            params: Parameters for the node
                of the form: {interval: Union[int, float],
                              ignore_nodes: list,
                              ignore_pipelines: list}
        """
        self.log(f"{self.__class__.__name__} started", level="info")
        self.metrics = {}  # type: ignore
        self.last_produce = -1.0
        self.interval = params.get("interval", 30)  # type: ignore
        self.ignore_nodes = params.get("ignore_nodes", [])  # type: ignore
        self.ignore_pipelines = params.get("ignore_pipelines", [])  # type: ignore # # pylint: disable=line-too-long
        self.input_datasets = cycle(self.consumers.keys())

        # Ignore messages from self to avoid infinite loop
        if self.__class__.__name__ not in self.ignore_nodes:
            self.ignore_nodes.append(self.__class__.__name__)

    def get_message(self) -> dict:
        """Get the next message from the list of input datasets.

        Returns:
            Message
        """
        return self.consumers[next(self.input_datasets)].consume(
            how="next", timeout=0
        )

    def produce_metric(self, value: Union[float, int], metadata: dict) -> None:
        """Produce a metric to the metrics dataset.

        Args:
            metric: Metric name
            value: Metric value
            metadata: Metric metadata
        """
        self.producers["metrics"].produce(
            {
                "metric": self.__class__.__name__,
                "interval": self.interval,
                "value": value,
                "metadata": metadata,
            }
        )
        self.last_produce = time.time()

    def seconds_since_produce(self) -> float:
        """Get the seconds passed since the last metric was produced.

        Returns:
            float: Time since last metric was produced
        """
        return time.time() - self.last_produce

    def validate_message(self, message: Optional[dict]) -> bool:
        """Validate the message.

        Args:
            message: Message

        Returns:
            True if message is valid else False
        """
        # Ignore None messages
        if message is None:
            return False

        # Ignore messages from ignored nodes and pipelines
        if (
            message["source_node"] in self.ignore_nodes
            or message["source_pipeline"] in self.ignore_pipelines
        ):
            return False

        return True

    def seconds_since_timestamp(self, timestamp: str) -> float:
        """Calculate the seconds elapsed since a given timestamp.

        Args:
            timestamp: Time in string format (YYYY-MM-DD HH:MM:SS.SSS)

        Returns:
            Time difference in seconds
        """
        return round(
            (
                datetime.now()
                - datetime.strptime(
                    timestamp, AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
                )
            ).seconds,
            2,
        )


class NodeHeartbeatInterval(Metrics):
    """Node heartbeat interval metric.

    Aggregates pipeline node heartbeat messages and publishes
    the last heartbeat message time to the node_activity dataset.

    Methods:
        _execute: Execute the node.
    """

    def _execute(self, params: Optional[dict] = None) -> Optional[bool]:
        """Execute the node.

        Args:
            params: Parameters for the node
        """
        # Consume messages
        message = self.get_message()
        if not self.validate_message(message):
            return None

        # Ignore messages that are not heartbeats
        if message["message"] != "heartbeat":
            return None

        # Update heartbeat time
        self.metrics[
            f"{message['source_pipeline']}.{message['source_node']}"
        ] = message["timestamp"]

        # Only produce metrics every interval
        if self.seconds_since_produce() < self.interval:
            return None

        # Produce current heartbeats
        for pipeline_node, heartbeat_time in self.metrics.items():
            self.produce_metric(
                value=self.seconds_since_timestamp(heartbeat_time),
                metadata={
                    "source_pipeline": pipeline_node.split(".")[0],
                    "source_node": pipeline_node.split(".")[1],
                },
            )
        return None


class PipelineHeartbeatInterval(Metrics):
    """Pipeline heartbeat metric.

    Aggregates pipeline node heartbeat messages and publishes
    the last heartbeat message time to the node_activity dataset.

    Methods:
        _execute: Execute the node.
    """

    def _execute(self, params: Optional[dict] = None) -> Optional[bool]:
        """Execute the node.

        Args:
            params: Parameters for the node
        """
        # Consume messages
        message = self.get_message()
        if not self.validate_message(message):
            return None

        # Ignore messages that do not contain a node heartbeat
        if (
            "metric" not in message["message"]
            or message["message"]["metric"] != "NodeHeartbeat"
        ):
            return None

        # Update value for time since last heartbeat
        self.metrics[f"{message['metadata']['source_pipeline']}"] = message[
            "value"
        ]

        # Only produce metrics every interval
        if self.seconds_since_produce() < self.interval:
            return None

        # Produce current heartbeats intervals
        for pipeline, elapsed_time in self.metrics.items():
            self.produce_metric(
                value=elapsed_time,
                metadata={"source_pipeline": pipeline},
            )
        return None


class LoggingLevelCounts(Metrics):
    """Logging level counts metrics.

    Methods:
        _execute: Execute the node.
    """

    def _execute(self, params: Optional[dict] = None) -> Optional[bool]:
        """Execute the node.

        Args:
            params: Parameters for the node
        """
        # Consume messages
        message = self.get_message()
        if not self.validate_message(message):
            return None

        # Process log messages
        if message["message"]["level"] not in self.metrics:
            self.metrics[message["message"]["level"]] = 0
        self.metrics[message["message"]["level"]] += 1

        # Only produce metrics every interval
        if self.seconds_since_produce() < self.interval:
            return None

        # Produce current log level counts every interval
        for log_level, count in self.metrics.items():
            self.produce_metric(
                value=count,
                metadata={"level": log_level},
            )
            # Reset log level count after producing
            self.metrics[log_level] = 0

        return None
