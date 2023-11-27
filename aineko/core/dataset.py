# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
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
import datetime
import json
import logging
from typing import Any, Dict, Optional

from confluent_kafka import (  # type: ignore
    Consumer,
    KafkaError,
    Message,
    Producer,
)

from aineko.config import AINEKO_CONFIG, DEFAULT_KAFKA_CONFIG

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class DatasetConsumer:
    """Wrapper class for Kafka consumer object.

    DatasetConsumer objects are designed to consume messages from a single
    dataset and will consume the next unconsumed message in the queue.

    When accessing kafka topics, prefixes will automatically be added to the
    dataset name as part of namespacing. For datasets defined in the pipeline
    config, `has_pipeline_prefix` will be set to `True`, so a dataset named
    `my_dataset` will point to a topic named `my_pipeline.my_dataset`.

    Optionally, a custom prefix can be provided that will apply to all datasets.
    In the above example, if the prefix is set to `test`, the topic name will
    be `test.my_pipeline.my_dataset`.

    Args:
        dataset_name: name of the dataset
        node_name: name of the node that is consuming the dataset
        pipeline_name: name of the pipeline
        dataset_config: dataset config
        bootstrap_servers: bootstrap_servers to connect to (e.g. "1.2.3.4:9092")
        prefix: prefix for topic name (<prefix>.<dataset_name>)
        has_pipeline_prefix: whether the dataset name has pipeline name prefix

    Attributes:
        consumer: Kafka consumer object
        cached: if the high watermark offset has been cached
        (updated when message consumed)

    Methods:
        consume: reads a message from the dataset
    """

    def __init__(
        self,
        dataset_name: str,
        node_name: str,
        pipeline_name: str,
        dataset_config: Dict[str, Any],
        bootstrap_servers: Optional[str] = None,
        prefix: Optional[str] = None,
        has_pipeline_prefix: bool = False,
    ):
        """Initialize the consumer."""
        self.pipeline_name = pipeline_name
        self.kafka_config = DEFAULT_KAFKA_CONFIG
        self.prefix = prefix
        self.has_pipeline_prefix = has_pipeline_prefix
        self.cached = False

        consumer_config = self.kafka_config.get("CONSUMER_CONFIG")
        # Overwrite bootstrap server with broker if provided
        if bootstrap_servers:
            consumer_config["bootstrap.servers"] = bootstrap_servers

        # Override default config with dataset specific config
        for param, value in dataset_config.get("params", {}).items():
            consumer_config[param] = value

        topic_name = dataset_name
        if has_pipeline_prefix:
            topic_name = f"{pipeline_name}.{dataset_name}"

        if self.prefix:
            consumer_config[
                "group.id"
            ] = f"{prefix}.{pipeline_name}.{node_name}"
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe([f"{prefix}.{topic_name}"])

        else:
            consumer_config["group.id"] = f"{pipeline_name}.{node_name}"
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe([topic_name])

        self.topic_name = topic_name

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
            logger.error(str(message.error()))
            return None

        # Convert message to dict
        message = message.value()
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        return json.loads(message)

    def _update_offset_to_latest(self) -> None:
        """Updates offset to latest.

        Note that the initial call, for this method might take
        a while due to consumer initialization.
        """
        partitions = self.consumer.assignment()
        # Initialize consumers if not already initialized by polling
        while not partitions:
            self.consumer.poll(timeout=0)
            partitions = self.consumer.assignment()

        for partition in partitions:
            partition.offset = (
                self.consumer.get_watermark_offsets(
                    partition, cached=self.cached
                )[1]
                - 1
            )

        self.consumer.assign(partitions)

    def consume(
        self,
        how: str = "next",
        timeout: Optional[int] = None,
    ) -> Optional[dict]:
        """Polls a message from the dataset.

        Args:
            how: how to read the message.
                "next": read the next message in the queue
                "last": read the last message in the queue
            timeout: seconds to poll for a resopnse from kafka broker.

        Returns:
            message from the dataset
        """
        if how not in ["next", "last"]:
            raise ValueError(f"Invalid how: {how}. Expected `next` or `last`.")

        timeout = timeout or self.kafka_config.get("CONSUMER_TIMEOUT")
        if how == "next":
            # next unread message from queue
            message = self.consumer.poll(timeout=timeout)

        if how == "last":
            # last message from queue
            self._update_offset_to_latest()
            message = self.consumer.poll(timeout=timeout)

        self.cached = True

        return self._validate_message(message)

    def _consume_message(self, how: str, timeout: Optional[int] = None) -> dict:
        """Calls the consume method and blocks until a message is returned.

        Args:
            how: See `consume` method for available options.

        Returns:
            message from dataset
        """
        while True:
            try:
                message = self.consume(how=how, timeout=timeout)
                if message is not None:
                    return message
            except KafkaError as e:
                if e.code() == "_MAX_POLL_EXCEEDED":
                    continue
                raise e

    def next(self) -> dict:
        """Wraps `consume(how="next")`, blocks until available.

        Returns:
            msg: message from the dataset
        """
        return self._consume_message(how="next")

    def last(self, timeout: int = 1) -> dict:
        """Wraps `consume(how="last")`, blocks until available.

        Returns:
            msg: message from the dataset
            timeout: seconds to poll for a resopnse from kafka broker.
        """
        return self._consume_message(how="last", timeout=timeout)

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

    See DatasetConsumer for prefix rules.

    Args:
        dataset_name: dataset name
        node_name: name of the node that is producing the message
        pipeline_name: name of the pipeline
        dataset_config: dataset config
        prefix: prefix for topic name (<prefix>.<dataset_name>)
        has_pipeline_prefix: whether the dataset name has pipeline name prefix

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
        prefix: Optional[str] = None,
        has_pipeline_prefix: bool = False,
    ):
        """Initialize the producer."""
        self.source_pipeline = pipeline_name
        self.dataset = dataset_name
        self.source_node = node_name
        self.prefix = prefix
        self.has_pipeline_prefix = has_pipeline_prefix

        # Create topic name based on prefix rules
        topic_name = dataset_name
        if has_pipeline_prefix:
            topic_name = f"{pipeline_name}.{topic_name}"
        if prefix:
            topic_name = f"{prefix}.{topic_name}"
        self.topic_name = topic_name

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
            logger.error("Message %s delivery failed: %s", message, err)

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
            topic=self.topic_name,
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
        raise ValueError(f"Invalid how: {how}. Expected 'next'.")


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
