

import datetime
import json
import time
from typing import Any, Optional, Literal, Union
from pydantic import BaseModel
from confluent_kafka import (  # type: ignore
    OFFSET_INVALID,
    Consumer,
    KafkaError,
    Message,
    Producer,
)
from confluent_kafka.admin import AdminClient, NewTopic  # type: ignore
from aineko.config import AINEKO_CONFIG, DEFAULT_KAFKA_CONFIG

from aineko.datasets.core import AbstractDataset, DatasetError, DatasetCreateStatus
import logging

logger = logging.getLogger(__name__)


class KafkaDatasetError(DatasetError):
    """General Exception for KafkaDataset errors."""

    pass


class KafkaCredentials(BaseModel):
    """Kafka credentials model."""

    bootstrap_servers: str = DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG").get('bootstrap.servers')
    security_protocol: Optional[str] = None
    sasl_mechanism: Optional[str] = None
    sasl_plain_username: Optional[str] = None
    sasl_plain_password: Optional[str] = None


class Kafka(AbstractDataset):
    """Kafka dataset."""

    def __init__(self, name: str, params: dict[str, Any]):
        self.name = name
        self.params = params
        self.type = "kafka"
        self.credentials = KafkaCredentials(**params)
        self._consumer = None
        self._producer = None
        self._create_admin_client()

    def _create(self, 
                create_topic:bool = False, 
                create_consumer:bool = False, 
                create_producer:bool = False) -> DatasetCreateStatus:
        """Create the dataset storage layer.

        This method creates the dataset topic in the Kafka cluster.

        Return status of dataset creation.
        """
        if create_topic and any([create_consumer, create_producer]):
            raise KafkaDatasetError("Cannot create topic and consumer/producer at the same time.")
        
        if create_topic:
            return self._create_topic()
        
        status_list = []
        if create_consumer:
            status_list.append(self._create_consumer())
        if create_producer:
            status_list.append(self._create_producer())
        return DatasetCreateStatus(dataset_name=self.name, status_list=status_list)

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
        self.producer.flush()

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
                    self.name,
                    e,
                )
                return None
            message = self._consumer.poll(timeout=timeout)

        self.cached = True

        return self._validate_message(message)


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

    def _create_consumer(self) -> DatasetCreateStatus:
        """Creates Kafka Consumer and subscribes to the dataset topic."""
        self._consumer = Consumer(
            self.topic_name,
            **self.credentials.dict(),
        )
        self._consumer.subscribe([self.topic_name])
        dataset_create_status = DatasetCreateStatus(dataset_name=f"{self.topic_name}_consumer")
        return dataset_create_status

    def _create_producer(self) -> DatasetCreateStatus:
        """Creates Kafka Producer."""
        self._producer = Producer(
            **self.credentials.dict(),
        )
        dataset_create_status = DatasetCreateStatus(dataset_name=f"{self.topic_name}_producer")
        return dataset_create_status

    def _create_topic(self, dataset_name: str) -> DatasetCreateStatus:
        """Creates Kafka topic for the dataset."""
        dataset_params = {
            **DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
            **dataset_config.get("params", {}),
        }

        # Configure dataset
        if self.dataset_prefix:
            topic_name = f"{self.dataset_prefix}.{dataset_name}"
        else:
            topic_name = dataset_name

        new_dataset = NewTopic(
            topic=topic_name,
            num_partitions=dataset_params.get("num_partitions"),
            replication_factor=dataset_params.get("replication_factor"),
            config=dataset_params.get("config"),
        )
        topic_to_future_map = self._admin_client.create_topics([new_dataset])
        dataset_create_status = DatasetCreateStatus(dataset_name, 
                                                    kafka_topic_to_future=topic_to_future_map)
        return dataset_create_status
        