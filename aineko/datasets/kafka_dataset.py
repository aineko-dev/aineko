

import datetime
import json
import time
from typing import Any, Optional
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

class KafkaDatasetError(DatasetError):
    """General Exception for KafkaDataset errors."""

    pass


class KafkaCredentials(BaseModel):
    """Kafka credentials model."""

    bootstrap_servers: str
    security_protocol: str
    sasl_mechanism: str
    sasl_plain_username: str
    sasl_plain_password: str


class KafkaDataset(AbstractDataset):
    """Kafka dataset."""

    def __init__(self, name: str, params: dict[str, Any]):
        self.name = name
        self.params = params
        self.type = "kafka"
        self.credentials = KafkaCredentials(**params)
        self._consumer = None
        self._producer = None
        self._create_admin_client()

    def _create(self, dataset_name: str) -> None:
        """Create the dataset storage layer.

        This method creates the dataset topic in the Kafka cluster.
        """
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
        cur_time = time.time()
        while True:
            if all(future.done() for future in topic_to_future_map.values()):
                # logger.info("{topic_name} created.")
                break
            if time.time() - cur_time > AINEKO_CONFIG.get(
                "DATASET_CREATION_TIMEOUT"
            ):
                raise TimeoutError(
                    "Timeout while creating Kafka datasets. "
                    "Please check your Kafka cluster."
                )

        self._create_consumer()
        self._create_producer()

    def _delete(self) -> None:
        """Delete the dataset."""
        self._admin_client.delete_topics([self.topic_name])

    def _read(self) -> Any:
        """Read the dataset."""
        self.consumer.consume()
        # next, last?

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

    def _create_admin_client(self):
        """Creates Kafka AdminClient."""
        self._admin_client = AdminClient(
            **self.credentials.dict(),
        )

    def _create_consumer(self):
        """Creates Kafka Consumer and subscribes to the dataset topic."""
        self._consumer = Consumer(
            self.topic_name,
            **self.credentials.dict(),
        )

        self._consumer.subscribe([self.topic_name])

    def _create_producer(self):
        """Creates Kafka Producer."""
        self._producer = Producer(
            **self.credentials.dict(),
        )
