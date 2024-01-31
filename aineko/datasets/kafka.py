# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Kafka Dataset.

Contains implmentation of Kafka dataset, which is a subclass of
AbstractDataset.
"""
import datetime
import json
import logging
from typing import Any, Literal, Optional, Union

from confluent_kafka import (  # type: ignore
    OFFSET_INVALID,
    Consumer,
    KafkaError,
    Message,
    Producer,
)
from confluent_kafka.admin import AdminClient, NewTopic  # type: ignore
from pydantic import BaseModel

from aineko.config import AINEKO_CONFIG, DEFAULT_KAFKA_CONFIG
from aineko.datasets.core import (
    AbstractDataset,
    DatasetCreateStatus,
    DatasetError,
)

logger = logging.getLogger(__name__)


class KafkaDatasetError(DatasetError):
    """General Exception for KafkaDataset errors."""

    pass


class KafkaCredentials(BaseModel):
    """Kafka credentials model."""

    bootstrap_servers: str = DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG").get(
        "bootstrap.servers"
    )
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_plain_username: Optional[str] = None
    sasl_plain_password: Optional[str] = None


class Kafka(AbstractDataset):
    """Kafka dataset."""

    def __init__(self, name: str, params: dict[str, Any]):
        """Initialize the dataset."""
        self.name = name
        self.topic_name = name
        self.params = params
        self.type = "kafka"
        self.credentials = KafkaCredentials(
            **params.get("kafka_credentials", {})
        )
        self.dataset_config = params
        self._consumer = None
        self._producer = None
        self._create_admin_client()

    def _create(
        self,
        create_topic: bool = False,
        create_consumer: bool = False,
        create_producer: bool = False,
        connection_params: dict[str, Any] | None = None,
    ) -> DatasetCreateStatus:
        """Create the dataset storage layer.

        This method creates the dataset topic in the Kafka cluster.

        Return status of dataset creation.
        """
        connection_params = connection_params or {}
        if create_topic and any([create_consumer, create_producer]):
            raise KafkaDatasetError(
                "Cannot create topic and consumer/producer at the same time."
            )

        if create_topic:
            return self._create_topic(
                dataset_name=self.name, dataset_config=self.dataset_config
            )

        status_list = []
        if create_consumer:
            status_list.append(
                self._create_consumer(consumer_params=connection_params)
            )
        if create_producer:
            status_list.append(
                self._create_producer(producer_params=connection_params)
            )
        return DatasetCreateStatus(
            dataset_name=self.name, status_list=status_list
        )

    def _delete(self) -> None:
        """Delete the dataset."""
        self._admin_client.delete_topics([self.topic_name])

    def _read(
        self, how: Literal["next", "last"], timeout: Optional[float] = None
    ) -> dict:
        """Calls the consume method and blocks until a message is returned.

        Args:
            how: See `consume` method for available options.

        Returns:
            message from dataset
        """
        while True:
            try:
                message = self._consume(how=how, timeout=timeout)
                if message is not None:
                    return message
            except KafkaError as e:
                if e.code() == "_MAX_POLL_EXCEEDED":
                    continue
                raise e

    def _write(self, message: dict, key: Optional[str] = None) -> None:
        """Produce a message to the dataset.

        Args:
            message: message to produce to the dataset
            key: key to use for the message
        """
        # Note, this will be re-written to use the dataset's schema,
        # without added metadata.
        message = {
            "timestamp": datetime.datetime.now().strftime(
                AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
            ),
            "dataset": self.dataset,
            "source_pipeline": self.source_pipeline,
            "source_node": self.source_node,
            "message": message,
        }
        self._producer.poll(0)

        key_bytes = str(key).encode("utf-8") if key is not None else None

        self._producer.produce(
            topic=self.topic_name,
            key=key_bytes,
            value=json.dumps(message).encode("utf-8"),
            callback=self._delivery_report,
        )
        self._producer.flush()

    def _describe(self) -> str:
        """Describe the dataset metadata."""
        describe_string = super()._describe()
        kafka_describe = "\n".join(
            [
                f"Kafka topic: {self.topic_name}",
                f"bootstrap_servers: {self.credentials.bootstrap_servers}",
            ]
        )
        describe_string += f"\n{kafka_describe}"
        return describe_string

    def _update_offset_to_latest(self) -> None:
        """Updates offset to latest.

        Note that the initial call, for this method might take
        a while due to consumer initialization.
        """
        partitions = self._consumer.assignment()
        # Initialize consumers if not already initialized by polling
        while not partitions:
            self._consumer.poll(timeout=0)
            partitions = self._consumer.assignment()

        for partition in partitions:
            high_offset = self._consumer.get_watermark_offsets(
                partition, cached=self.cached
            )[1]

            # Invalid high offset can be caused by various reasons,
            # including rebalancing and empty topic. Default to -1.
            if high_offset == OFFSET_INVALID:
                logger.error(
                    "Invalid offset received for consumer: %s",
                    self.consumer_name,
                )
                partition.offset = -1
            else:
                partition.offset = high_offset - 1

        self._consumer.assign(partitions)

    def _consume(
        self,
        how: Literal["next", "last"] = "next",
        timeout: Optional[float] = None,
    ) -> Optional[dict]:
        """Polls a message from the dataset.

        If the consume method is last but the method encounters
        an error trying to udpdate the offset to latest, it will
        poll and return None.

        Args:
            how: how to read the message.
                "next": read the next message in the queue
                "last": read the last message in the queue
            timeout: seconds to poll for a response from kafka broker.
                If using how="last", set to bigger than 0.

        Returns:
            message from the dataset

        Raises:
            ValueError: if how is not "next" or "last"
        """
        if how not in ["next", "last"]:
            raise ValueError(f"Invalid how: {how}. Expected `next` or `last`.")

        timeout = timeout or self.kafka_config.get("CONSUMER_TIMEOUT")
        if how == "next":
            # next unread message from queue
            message = self._consumer.poll(timeout=timeout)

        if how == "last":
            # last message from queue
            try:
                self._update_offset_to_latest()
            except KafkaError as e:
                logger.error(
                    "Error updating offset to latest for consumer %s: %s",
                    self.consumer_name,
                    e,
                )
                return None
            message = self._consumer.poll(timeout=timeout)

        self.cached = True

        return self._validate_message(message)

    @staticmethod
    def _validate_message(
        message: Optional[Message] = None,
    ) -> Optional[dict]:
        """Checks if a message is valid and converts it to appropriate format.

        Args:
            message: message to check

        Returns:
            message if valid, None if not
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

    def next(self) -> dict:
        """Consumes the next message from the dataset.

        Wraps the `consume(how="next")` method. It implements a
        block that waits until a message is received before returning it.
        This method ensures that every message is consumed, but the consumed
        message may not be the most recent message if the consumer is slower
        than the producer.

        This is useful when the timeout is short and you expect the consumer
        to often return `None`.

        Returns:
            message from the dataset
        """
        return self._read(how="next")

    def last(self, timeout: int = 1) -> dict:
        """Consumes the last message from the dataset.

        Wraps the `consume(how="last")` method. It implements a
        block that waits until a message is received before returning it.
        This method ensures that the consumed message is always the most
        recent message. If the consumer is slower than the producer, messages
        might be skipped. If the consumer is faster than the producer,
        messages might be repeated.

        This is useful when the timeout is short and you expect the consumer
        to often return `None`.

        Note: The timeout must be greater than 0 to prevent
        overwhelming the broker with requests to update the offset.

        Args:
            timeout: seconds to poll for a response from kafka broker.
                Must be >0.

        Returns:
            message from the dataset

        Raises:
            ValueError: if timeout is <= 0
        """
        if timeout <= 0:
            raise ValueError(
                "Timeout must be > 0 when consuming the last message."
            )
        return self._read(how="last", timeout=timeout)

    def consume_all(self, end_message: Union[str, bool] = False) -> list:
        """Reads all messages from the dataset until a specific one is found.

        Args:
            end_message: Message to trigger the completion of consumption

        Returns:
            list of messages from the dataset
        """
        messages = []
        while True:
            message = self._consume()
            if message is None:
                continue
            if message["message"] == end_message:
                break
            messages.append(message)
        return messages

    # Create methods

    def _create_admin_client(self):
        """Creates Kafka AdminClient."""
        # remove 'bootstrap.servers' from credentials
        self._admin_client = AdminClient(
            DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG"),
        )

    def _create_consumer(
        self, consumer_params: dict[str, Any]
    ) -> DatasetCreateStatus:
        """Creates Kafka Consumer and subscribes to the dataset topic.

        consumer_params is a dict of the form:
        {   "dataset_name":str,
            "node_name":str,
            "pipeline_name":str,
            "prefix":Optional[str],
            "has_pipeline_prefix":bool,
            "consumer_config:" DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG"),
        }
        """
        # build topic name from prefix + pipeline_name + name,
        # depending on consumer params:
        dataset_name = consumer_params.get("dataset_name")
        node_name = consumer_params.get("node_name")
        pipeline_name = consumer_params.get("pipeline_name")
        prefix = consumer_params.get("prefix")
        has_pipeline_prefix = consumer_params.get("has_pipeline_prefix")
        consumer_config = consumer_params.get(
            "consumer_config", DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG")
        )

        if has_pipeline_prefix:
            self.topic_name = f"{pipeline_name}.{dataset_name}"
        else:
            self.topic_name = dataset_name
        if prefix:
            self.consumer_name = f"{prefix}.{pipeline_name}.{node_name}"
            consumer_config["group.id"] = self.consumer_name
            self._consumer = Consumer(consumer_config)
            self._consumer.subscribe([f"{prefix}.{self.topic_name}"])

        else:
            self.consumer_name = f"{pipeline_name}.{node_name}"
            consumer_config["group.id"] = f"{pipeline_name}.{node_name}"
            self._consumer = Consumer(consumer_config)
            self._consumer.subscribe([self.topic_name])

        dataset_create_status = DatasetCreateStatus(
            dataset_name=f"{self.topic_name}_consumer"
        )
        return dataset_create_status

    def _create_producer(
        self, producer_params: dict[str, Any]
    ) -> DatasetCreateStatus:
        """Creates Kafka Producer.

        Producer params is a dict of the form:
        {
            dataset_name:str,
            pipeline_name:str,
            prefix:Optional[str],
            has_pipeline_prefix:bool,
            producer_config:DEFAULT_KAFKA_CONFIG.get("PRODUCER_CONFIG"),
        }
        """
        has_pipeline_prefix = producer_params.get("has_pipeline_prefix")
        pipeline_name = producer_params.get("pipeline_name")
        dataset_name = producer_params.get("dataset_name")
        prefix = producer_params.get("prefix")
        # create topic name here:
        topic_name = dataset_name
        if has_pipeline_prefix:
            topic_name = f"{pipeline_name}.{topic_name}"
        if prefix:
            topic_name = f"{prefix}.{topic_name}"
        self.topic_name = topic_name
        producer_config = producer_params.get(
            "producer_config", DEFAULT_KAFKA_CONFIG.get("PRODUCER_CONFIG")
        )
        self._producer = Producer(
            **producer_config,
        )
        dataset_create_status = DatasetCreateStatus(
            dataset_name=f"{self.topic_name}_producer"
        )
        return dataset_create_status

    def _create_topic(
        self, dataset_name: str, dataset_config: dict[str, Any]
    ) -> DatasetCreateStatus:
        """Creates Kafka topic for the dataset."""
        if "dataset_prefix" in dataset_config:
            dataset_prefix = dataset_config.pop("dataset_prefix")
        else:
            dataset_prefix = None

        dataset_params = {
            **DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
            **dataset_config.get("params", {}),
        }

        # Configure dataset
        if dataset_prefix:
            topic_name = f"{dataset_prefix}.{dataset_name}"
        else:
            topic_name = dataset_name

        new_dataset = NewTopic(
            topic=topic_name,
            num_partitions=dataset_params.get("num_partitions"),
            replication_factor=dataset_params.get("replication_factor"),
            config=dataset_params.get("config"),
        )
        topic_to_future_map = self._admin_client.create_topics([new_dataset])
        dataset_create_status = DatasetCreateStatus(
            dataset_name, kafka_topic_to_future=topic_to_future_map
        )
        return dataset_create_status

# pylint: enable=too-few-public-methods
# pylint: disable=unused-argument
class FakeDatasetInput:
    """Fake dataset Input (consumer) for testing purposes.

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

    def read(
        self,
        how: str = "next",
        timeout: Optional[float] = None,
    ) -> Optional[dict]:
        """Reads a message from the dataset.

        Args:
            how: how to read the message
                "next": read the next message in the queue
                ":last": read the last message in the queue

        Returns:
            next or last value in self.values

        Raises:
            ValueError: if how is not "next" or "last"
        """
        if how not in ["next", "last"]:
            raise ValueError(f"Invalid how: {how}. Expected 'next' or 'last'.")

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
        if how == "last":
            if self.values:
                return self.values[-1]

        return None

    def next(self) -> Optional[dict]:
        """Wraps `consume(how="next")`, blocks until available.

        Returns:
            msg: message from the dataset
        """
        return self.read(how="next")

    def last(self, timeout: float = 1) -> Optional[dict]:
        """Wraps `consume(how="last")`, blocks until available.

        Returns:
            msg: message from the dataset
        """
        return self.read(how="last", timeout=timeout)
    

class FakeDatasetOutput:
    """Fake dataset Output (producer) for testing purposes.

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

    def write(self, message: Any) -> None:
        """Stores message in self.values.

        Args:
            message: message to produce.
        """
        self.values.append(message)
