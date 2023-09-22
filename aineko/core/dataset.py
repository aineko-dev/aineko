"""Module for managing datasets.

Datasets are Kafka topics that are used to
communicate between nodes in the pipeline. The dataset module provides
a wrapper for the Kafka consumer and producer objects.

Note:
e.g. message:
{
    # Inferred metadata
    "timestamp": "2020-01-01 00:00:00"
    "dataset": "dataset_1",
    "source_node": "node_1",

    # User defined message
    "message": {...},
}
"""
import ast
import datetime
import json
from typing import Any, Dict, Optional

from confluent_kafka import Consumer, Message, Producer

from aineko.config import AINEKO_CONFIG, DEFAULT_KAFKA_CONFIG


# pylint: disable=too-few-public-methods
class DatasetConsumer:
    """Wrapper class for Kafka consumer object.

    DatasetConsumer objects are designed to consume messages from a single
    dataset and can consume messages in two different ways:
        "next": read the next unconsumed message in the queue
        "last": read the latest message in the queue

    Args:
        dataset_name: name of the dataset
        node_name: name of the node that is consuming the dataset
        pipeline_name: name of the pipeline
        dataset_config: dataset config
        broker: broker to connect to (ip and port: "54.88.142.21:9092")

    Attributes:
        consumer: Kafka consumer object

    Methods:
        consume: reads a message from the dataset
    """

    def __init__(
        self,
        dataset_name: str,
        node_name: str,
        pipeline_name: str,
        dataset_config: Dict[str, Any],
        broker: Optional[str] = None,
    ):
        """Initialize the consumer."""
        # Assign dataset name
        self.pipeline_name = pipeline_name

        # Assign kafka config
        self.kafka_config = DEFAULT_KAFKA_CONFIG

        # Set consumer parameters
        consumer_config = self.kafka_config.get("CONSUMER_CONFIG")

        # Overwrite broker target if provided
        if broker:
            consumer_config["bootstrap.servers"] = broker

        # Override default config with dataset specific config
        for param, value in dataset_config.get("params", {}).items():
            if param in self.kafka_config.get("CONSUMER_OVERRIDABLES"):
                consumer_config[param] = dataset_config["params"][value]

        # Add consumer group id based on node name
        consumer_config["group.id"] = f"{self.pipeline_name}.{node_name}"

        # Create consumer
        self.consumer = Consumer(consumer_config)
        self.consumer.subscribe([dataset_name])

    @staticmethod
    def _validate_message(
        message: Optional[Message] = None,
    ) -> Optional[dict]:
        """Checks if a message is valid and converts it to appropriate format.

        Args:
            message: message to check

        Returns:
            message: message if valid, None if not
        """
        # Check if message is valid
        if message is None or message.value() is None:
            return None

        # Check if message is an error
        if message.error():
            print(message.error())
            return None

        # Convert message to dict
        message = message.value()
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        return ast.literal_eval(message)

    def consume(
        self,
        how: str = "next",
        timeout: Optional[int] = None,
    ) -> Optional[dict]:
        """Reads a message from the dataset.

        Args:
            how: how to read the message
                "next": read the next message in the queue

        Returns:
            msg: message from the dataset
        """
        timeout = timeout or self.kafka_config.get("CONSUMER_TIMEOUT")
        if how == "next":
            # next unread message from queue
            message = self._validate_message(
                self.consumer.poll(timeout=timeout)
            )
        else:
            raise ValueError(f"Invalid how: {how}. Expecected 'next'.")

        return message

    def consume_all(self, end_message: str | bool = False) -> list:
        """Reads all messages from the dataset until a specific one is found.

        Args:
            end_message: Message to trigger the completion of consumption

        Returns:
            list: list of messages from the dataset
        """
        messages = []
        while True:
            message = self.consume()
            if message is None:
                continue
            if message["message"] == end_message:
                break
            messages.append(message)
        return messages


class DatasetProducer:
    """Wrapper class for Kafka producer object.

    Args:
        dataset_name: dataset name
        node_name: name of the node that is producing the message
        pipeline_name: name of the pipeline
        dataset_config: dataset config

    Attributes:
        producer: Kafka producer object

    Methods:
        produce: produce a message to the dataset
    """

    def __init__(
        self,
        dataset_name: str,
        node_name: str,
        pipeline_name: str,
        dataset_config: Dict[str, Any],
    ):
        """Initialize the producer."""
        # Assign dataset name
        self.source_pipeline = pipeline_name
        self.dataset = dataset_name
        self.source_node = node_name

        # Assign kafka config
        self.kafka_config = DEFAULT_KAFKA_CONFIG

        # Set producer parameters
        producer_config = self.kafka_config.get("PRODUCER_CONFIG")

        # Override default config with dataset specific config
        if "params" in dataset_config:
            for param in self.kafka_config.get("PRODUCER_OVERRIDABLES"):
                if param in dataset_config["params"]:
                    producer_config[param] = dataset_config["params"][param]

        # Create producer
        self.producer = Producer(producer_config)

    @staticmethod
    def _delivery_report(err: Any, message: Message) -> None:
        """Called once for each message produced to indicate delivery result.

        Triggered by poll() or flush().

        Args:
            err: error message
            message: message object from Kafka
        """
        if err is not None:
            print(f"Message {message} delivery failed: {err}")

    def produce(self, message: dict, key: Optional[str] = None) -> None:
        """Produce a message to the dataset.

        Args:
            message: message to produce to the dataset
            key: key to use for the message
        """
        message = {
            "timestamp": datetime.datetime.now().strftime(
                AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
            ),
            "dataset": self.dataset,
            "source_pipeline": self.source_pipeline,
            "source_node": self.source_node,
            "message": message,
        }
        self.producer.poll(0)

        key_bytes = str(key).encode("utf-8") if key is not None else None

        self.producer.produce(
            topic=self.dataset,
            key=key_bytes,
            value=json.dumps(message).encode("utf-8"),
            callback=self._delivery_report,
        )
        self.producer.flush()


# pylint: enable=too-few-public-methods
# pylint: disable=unused-argument
class FakeDatasetConsumer:
    """Fake dataset consumer for testing purposes.

    The class will store in its state the list of values to feed the node,
    and pop each value everytime the consume method is called.

    Args:
        dataset_name: name of the dataset
        node_name: name of the node that is consuming the dataset
        values: list of values to feed the node

    Attributes:
        dataset_name (str): name of the dataset
        node_name (str): name of the node that is consuming the dataset
        values (list): list of mock data values to feed the node
        empty (bool): True if the list of values is empty, False otherwise
    """

    def __init__(self, dataset_name: str, node_name: str, values: list):
        """Initialize the consumer."""
        self.dataset_name = dataset_name
        self.node_name = node_name
        self.values = values
        self.empty = False

    def consume(
        self,
        how: str = "next",
        timeout: Optional[int] = None,
    ) -> Optional[dict]:
        """Reads a message from the dataset.

        Args:
            how: how to read the message
                "next": read the next message in the queue

        Returns:
            next value in self.values

        Raises:
            ValueError: if how is not "next"
        """
        if how == "next":
            remaining = len(self.values)
            if remaining > 0:
                if remaining == 1:
                    self.empty = True
                return {
                    "timestamp": datetime.datetime.now().strftime(
                        AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
                    ),
                    "message": self.values.pop(0),
                    "source_node": "test",
                    "source_pipeline": "test",
                }
            else:
                return None
        raise ValueError(f"Invalid how: {how}. Expecected 'next'.")


class FakeDatasetProducer:
    """Fake dataset producer for testing purposes.

    The class will store in its state the list of values produced
    by the node.

    Args:
        dataset_name: name of the dataset
        node_name: name of the node that is producing the dataset

    Attributes:
        dataset_name (str): name of the dataset
        node_name (str): name of the node that is producing the dataset
        values (list): list of mock data values produced by the node
    """

    def __init__(self, dataset_name: str, node_name: str):
        """Initialize the producer."""
        self.dataset_name = dataset_name
        self.node_name = node_name
        self.values = []  # type: ignore

    def produce(self, message: Any) -> None:
        """Stores message in self.values.

        Args:
            message: message to produce.
        """
        self.values.append(message)
