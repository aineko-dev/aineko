# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Kafka Dataset.

Contains Kafka dataset, a subclass of AbstractDataset.

The storage layer for a Kafka dataset is a Kafka topic.

The query layer for reading and writing to the topic
is a Kafka consumer and producer, respectively.
"""
import datetime
import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional, Union

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
from aineko.core.dataset import (
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


class KafkaParams(BaseModel):
    """Base class for query layer params for KafkaDataset.

    Used to initialize a Kafka Consumer or Producer.
    """

    dataset_name: str
    node_name: str
    pipeline_name: str
    prefix: Optional[str] = None
    has_pipeline_prefix: bool


class ConsumerParams(KafkaParams):
    """Parameters for initializing a Kafka Consumer.

    Passed in as connection_params when calling
        ```python
        self.initialize(create="consumer",
                      connection_params=ConsumerParams(...))
        ```
    """

    consumer_config: Dict[str, Any] = DEFAULT_KAFKA_CONFIG.get(
        "CONSUMER_CONFIG"
    )


class ProducerParams(KafkaParams):
    """Parameters for initializing a Kafka Producer.

    Passed in as conection_params when calling
        ```python
        self.initialize(create="producer",
                      connection_params=ProducerParams(...))
        ```
    """

    producer_config: Dict[str, Any] = DEFAULT_KAFKA_CONFIG.get(
        "PRODUCER_CONFIG"
    )


class TopicParams(BaseModel):
    """Parameters for initializing a Kafka Topic.

    Passed in as connection_params when calling
        ```python
        self.create(topic_params=TopicParams(...))
        ```
    """

    dataset_prefix: Optional[str] = None
    dataset_config: Dict[str, Any] = {}


class KafkaDataset(AbstractDataset):
    """Kafka dataset.

    Dataset Storage Layer is a Kafka topic.

    Dataset Query Layer is a Kafka Consumer and Producer.

    `read` method consumes from a Kakfa topic.

    `write` method produces to a Kafka topic.

    `create` method creates the dataset topic in the Kafka cluster.

    `initialize` method can be used to create a consumer or producer.

    `delete` method deletes the dataset topic in the Kafka cluster.

    `exists` method checks if the dataset topic exists.

    Args:
        name: name of the dataset
        params: dataset configuration parameters

    Attributes:
        name (str): name of the dataset
        topic_name (str): name of the Kafka topic
        params (dict): dataset configuration parameters
        type (str): type of the dataset
        credentials (KafkaCredentials): Kafka credentials
        dataset_config (dict): dataset configuration
        _consumer (Consumer): Kafka consumer
        _producer (Producer): Kafka producer
        _admin_client (AdminClient): Kafka AdminClient
        cached (bool): True if the consumer has been polled, False otherwise
        location (str): location of the dataset
        consumer_name (str): name of the consumer

    Raises:
        KafkaDatasetError: if an error occurs while creating the dataset
    """

    def __init__(self, name: str, params: Dict[str, Any]):
        """Initialize the dataset."""
        self.name = name
        self.topic_name = name
        self.params = params
        self.type = "kafka"
        self.consumer_name: Optional[str] = None
        self.credentials = KafkaCredentials(
            **params.get("kafka_credentials", {})
        )
        self.dataset_config = params
        self.location = self._update_location()
        self.cached = False
        self.source_node: str
        self.source_pipeline: str
        self._consumer: Consumer
        self._producer: Producer
        self._create_admin_client()

    def create(
        self,
        topic_params: TopicParams = TopicParams(),
    ) -> DatasetCreateStatus:
        """Create the dataset storage layer kafka topic.

        Args:
            topic_params: initialization parameters for the dataset topic

        Returns:
          status of dataset creation.
        """
        return self._create_topic(
            dataset_name=self.name, topic_params=topic_params
        )

    def initialize(
        self,
        connection_params: Union[ConsumerParams, ProducerParams],
        create: Literal["consumer", "producer"],
    ) -> None:
        """Create query layer reader or writer for the dataset.

        This method can be called in 2 different ways:

            1. `self.initialize(create="consumer",
            connection_params=ConsumerParams(...))`:
                creates a Kafka Consumer and subscribes to the
                dataset topic.

            2. `self.initialize(create="producer",
            connection_params=ProducerParams(...)`:
                creates a Kafka Producer.

        Args:
            create: if "consumer", create a Kafka Consumer and
                subscribe to the dataset topic. If "producer",
                create a Kafka Producer
            connection_params: connection parameters for the dataset

        Raises:
            KafkaDatasetError: if an error occurs while creating the consumer
                or producer
        """
        if create == "consumer":
            try:
                if not isinstance(connection_params, ConsumerParams):
                    raise KafkaDatasetError(
                        "Invalid connection_params for creating consumer."
                    )
                self._create_consumer(consumer_params=connection_params)
                logger.info("Consumer for %s created.", self.topic_name)
            except KafkaError as err:
                raise KafkaDatasetError(
                    f"Error creating consumer for {self.topic_name}: {str(err)}"
                ) from err
            return
        elif create == "producer":
            try:
                if not isinstance(connection_params, ProducerParams):
                    raise KafkaDatasetError(
                        "Invalid connection_params for creating producer."
                    )
                self._create_producer(producer_params=connection_params)
                logger.info("Producer for %s created.", self.topic_name)
            except KafkaError as err:
                raise KafkaDatasetError(
                    f"Error creating producer for {self.topic_name}: {str(err)}"
                ) from err
            return

    def delete(self) -> None:
        """Delete the dataset topic from the Kafka cluster.

        Raises:
            KafkaDatasetError: if an error occurs while deleting the topic
        """
        try:
            self._admin_client.delete_topics([self.topic_name])
        except Exception as err:
            raise KafkaDatasetError(
                f"Error deleting topic {self.topic_name}: {str(err)}"
            ) from err

    def read(
        self,
        how: Literal["next", "last"],
        timeout: Optional[float] = None,
        block: bool = False,
    ) -> Optional[Dict]:
        """Read the dataset message via the query layer.

        Args:
            how: how to read the message
                "next": read the next message in the queue
                ":last": read the last message in the queue
            timeout: seconds to poll for a response from kafka broker.
                If using how="last", set to bigger than 0.
            block: if True, block until a message is received

        Returns:
            message from the dataset

        Raises:
            ValueError: if how is not "next" or "last"
        """
        if block:
            return self._consume_message(how=how, timeout=timeout)
        else:
            return self._consume(how=how, timeout=timeout)

    def _consume_message(
        self, how: Literal["next", "last"], timeout: Optional[float] = None
    ) -> Dict:
        """Calls the consume method and blocks until a message is returned.

        Args:
            how: See `_consume` method for available options.

        Returns:
            message from dataset

        Raises:
            KafkaDatasetError: if an error occurs while reading the topic
        """
        while True:
            try:
                message = self._consume(how=how, timeout=timeout)
                if message is not None:
                    return message
            except KafkaError as err:
                if err.code() == "_MAX_POLL_EXCEEDED":
                    continue
                raise KafkaDatasetError(
                    f"Error occurred while reading topic: {str(err)}"
                ) from err

    def write(self, msg: Dict, key: Optional[str] = None) -> None:
        """Produce a message to the dataset.

        Args:
            msg: message to produce to the dataset
            key: key to use for the message

        Raises:
            KafkaDatasetError: if an error occurs while writing to the topic
        """
        # Note, this will be re-written to use the dataset's schema,
        # without added metadata.
        message = {
            "timestamp": datetime.datetime.now().strftime(
                AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
            ),
            "dataset": self.name,
            "source_pipeline": self.source_pipeline,
            "source_node": self.source_node,
            "message": msg,
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

    def exists(self) -> bool:
        """Check if the dataset exists.

        Returns:
            True if the dataset topic exists, False otherwise
        """
        return self.topic_name in self._admin_client.list_topics().topics

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
    ) -> Optional[Dict]:
        """Polls a message from the dataset.

        If the consume method is last but the method encounters
        an error trying to update the offset to latest, it will
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

        timeout = timeout or DEFAULT_KAFKA_CONFIG.get("CONSUMER_TIMEOUT")
        if how == "next":
            # next unread message from queue
            message = self._consumer.poll(timeout=timeout)

        if how == "last":
            # last message from queue
            try:
                self._update_offset_to_latest()
            except KafkaError as err:
                logger.error(
                    "Error updating offset to latest for consumer %s: %s",
                    self.consumer_name,
                    err,
                )
                return None
            message = self._consumer.poll(timeout=timeout)

        self.cached = True

        return self._validate_message(message)

    @staticmethod
    def _validate_message(
        message: Optional[Message] = None,
    ) -> Optional[Dict]:
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

    def next(self) -> Dict:
        """Consumes the next message from the dataset.

        Wraps the `_consume_message(how="next")` method. It implements a
        block that waits until a message is received before returning it.
        This method ensures that every message is consumed, but the consumed
        message may not be the most recent message if the consumer is slower
        than the producer.

        This is useful when the timeout is short and you expect the consumer
        to often return `None`.

        Returns:
            message from the dataset
        """
        return self._consume_message(how="next", timeout=-1)

    def last(self, timeout: int = 1) -> Dict:
        """Consumes the last message from the dataset.

        Wraps the `_consume_message(how="last")` method. It implements a
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
        return self._consume_message(how="last", timeout=timeout)

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

    def _create_admin_client(self) -> None:
        """Creates Kafka AdminClient.

        The AdminClient can be used to create and delete
        Kafka topics.

        Raises:
            KafkaDatasetError: if an error occurs while creating
                the AdminClient
        """
        try:
            self._admin_client = AdminClient(
                DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG"),
            )
        except KafkaError as err:
            raise KafkaDatasetError(
                f"Error creating Kafka AdminClient: {str(err)}"
            ) from err

    def _create_consumer(
        self, consumer_params: ConsumerParams
    ) -> DatasetCreateStatus:
        """Creates Kafka Consumer and subscribes to the dataset topic.

        Used to read (consume) messages from the dataset topic.

        Args:
            consumer_params: parameters for initializing the consumer

        Returns:
            status of dataset creation
        """
        dataset_name = consumer_params.dataset_name
        node_name = consumer_params.node_name
        pipeline_name = consumer_params.pipeline_name
        prefix = consumer_params.prefix
        has_pipeline_prefix = consumer_params.has_pipeline_prefix
        consumer_config = consumer_params.consumer_config

        self.topic_name = (
            f"{pipeline_name}.{dataset_name}"
            if has_pipeline_prefix
            else dataset_name
        )

        if prefix:
            self.consumer_name = f"{prefix}.{pipeline_name}.{node_name}"
            consumer_topic = f"{prefix}.{self.topic_name}"
        else:
            self.consumer_name = f"{pipeline_name}.{node_name}"
            consumer_topic = self.topic_name

        consumer_config["group.id"] = self.consumer_name
        self._consumer = Consumer(consumer_config)
        self._consumer.subscribe([consumer_topic])

        dataset_create_status = DatasetCreateStatus(
            dataset_name=f"{self.topic_name}_consumer"
        )
        return dataset_create_status

    def _create_producer(
        self, producer_params: ProducerParams
    ) -> DatasetCreateStatus:
        """Creates Kafka Producer.

        Used to write (produce) messages to the dataset topic.

        Args:
            producer_params: parameters for initializing the producer

        Returns:
            status of dataset creation
        """
        has_pipeline_prefix = producer_params.has_pipeline_prefix
        node_name = producer_params.node_name
        pipeline_name = producer_params.pipeline_name
        dataset_name = producer_params.dataset_name
        prefix = producer_params.prefix
        # create topic name here:
        topic_name = dataset_name
        self.source_node = node_name
        self.source_pipeline = pipeline_name
        if has_pipeline_prefix:
            topic_name = f"{pipeline_name}.{topic_name}"
        if prefix:
            topic_name = f"{prefix}.{topic_name}"
        self.topic_name = topic_name
        producer_config = producer_params.producer_config
        self._producer = Producer(
            **producer_config,
        )
        dataset_create_status = DatasetCreateStatus(
            dataset_name=f"{self.topic_name}_producer"
        )
        return dataset_create_status

    def _create_topic(
        self, dataset_name: str, topic_params: TopicParams
    ) -> DatasetCreateStatus:
        """Creates Kafka topic for the dataset storage layer.

        Args:
            dataset_name: name of the dataset
            topic_params: initialization parameters for the dataset topic

        Returns:
            status of dataset creation
        """
        dataset_prefix = topic_params.dataset_prefix
        dataset_config = topic_params.dataset_config
        if not dataset_config:
            dataset_config = self.dataset_config
        dataset_params = {
            **DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
            **dataset_config,
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

    def _update_location(self) -> str:
        """Updates the location of the dataset to `self.location`.

        Updates the location for the DEFAULT_KAFKA_CONFIG
        variable and the credentials to the `self.location` value.

        If no location is provided in the dataset config, it uses
        the value from the DEFAULT_KAFKA_CONFIG.

        DEFAULT_KAFKA_CONFIG uses the environment variable
        KAFKA_CONFIG_BOOTSTRAP_SERVERS, or a default value.

        Precedence is:
          1. dataset config location >
          2. environment variable >
          3. default value (localhost:9092)
        """
        location: Optional[str] = self.params.get("location")
        if not location:
            location = os.getenv(
                "KAFKA_CONFIG_BOOTSTRAP_SERVERS",
                DEFAULT_KAFKA_CONFIG.BROKER_CONFIG.get(
                    "bootstrap.servers", "localhost:9092"
                ),
            )

        self.credentials.bootstrap_servers = location
        DEFAULT_KAFKA_CONFIG.BROKER_CONFIG["bootstrap.servers"] = location
        DEFAULT_KAFKA_CONFIG.CONSUMER_CONFIG["bootstrap.servers"] = location
        DEFAULT_KAFKA_CONFIG.PRODUCER_CONFIG["bootstrap.servers"] = location
        return location


class FakeKafka:
    """Fake Kafka dataset class for testing.

    The class can be used as both a reader and a writer for testing
    purposes.

    As a reader (consumer), the class will store in its state the list
    of values to feed the node, and pop each value everytime the read
    method is called.

    As a writer (producer), The class will store in its state the list
    of values produced by the node.

    Args:
        dataset_name: name of the dataset
        node_name: name of the node that is consuming the dataset
        input_values: list of values to feed the node

    Attributes:
        dataset_name (str): name of the dataset
        node_name (str): name of the node that is consuming the dataset
        input_values (list): list of mock data values to feed the node
        empty (bool): True if the list of values is empty, False otherwise
        output_values (list): list of mock data values produced by the node
    """

    def __init__(
        self,
        dataset_name: str,
        node_name: str,
        input_values: Optional[List] = None,
    ):
        """Initialize the fake dataset."""
        self.dataset_name = dataset_name
        self.node_name = node_name
        self.input_values = input_values or []
        self.empty = False
        self.output_values = []  # type: ignore

    def read(
        self,
        how: str = "next",
        timeout: Optional[float] = None,
    ) -> Optional[Dict]:
        """Reads a message from the dataset.

        Args:
            how: how to read the message
                "next": read the next message in the queue
                "last": read the last message in the queue

            timeout: seconds to poll for a response from kafka broker.
                If using how="last", set to bigger than 0.

        Returns:
            next or last value in self.input_values

        Raises:
            ValueError: if how is not "next" or "last"
        """
        del timeout  # unused because this is a fake dataset
        if how not in ["next", "last"]:
            raise ValueError(f"Invalid how: {how}. Expected 'next' or 'last'.")

        if how == "next":
            remaining = len(self.input_values)
            if remaining > 0:
                if remaining == 1:
                    self.empty = True
                return {
                    "timestamp": datetime.datetime.now().strftime(
                        AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
                    ),
                    "message": self.input_values.pop(0),
                    "source_node": "test",
                    "source_pipeline": "test",
                }
        if how == "last":
            if self.input_values:
                return self.input_values[-1]

        return None

    def next(self) -> Optional[Dict]:
        """Wraps `read(how="next")`, blocks until available.

        Returns:
            msg: message from the dataset
        """
        return self.read(how="next")

    def last(self, timeout: float = 1) -> Optional[Dict]:
        """Wraps `read(how="last")`, blocks until available.

        Returns:
            msg: message from the dataset
        """
        return self.read(how="last", timeout=timeout)

    def write(self, message: Dict) -> None:
        """Stores message in self.input_values.

        Args:
            message: message to write.
        """
        self.output_values.append(message)
