# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for KafkaDataset topic creation."""

import json
import sys

import pytest
from confluent_kafka import KafkaException

from aineko.core.dataset import AbstractDataset
from aineko.datasets.kafka import KafkaDataset
from aineko.models.dataset_config_schema import DatasetConfig


def generate_dict_of_bytesize(approx_size_bytes: int) -> dict:
    """Generate a dict of a given size in bytes when produced as a message.

    This function can be used to generate a dictionary with a size close to the
    desired size when serialized as a JSON message. This is useful for testing
    the maximum message size that can be written to a Kafka topic.

    Args:
        approx_size_bytes: The approximate size in bytes of the message.

    Returns:
        The dictionary with a size close to the desired size.
    """
    test_dict = {}
    batch_size = 10000  # Adjust based on precision-speed tradeoff

    # Initialize an empty JSON string representation of the dictionary
    json_str = json.dumps(test_dict)

    while sys.getsizeof(json_str) < approx_size_bytes:
        next_key = len(test_dict)
        for i in range(batch_size):
            test_dict[next_key + i] = "a"  # Populate with dummy data

        # Update the JSON string representation after adding the batch
        json_str = json.dumps(test_dict)

        # Check if the next addition will exceed the desired size
        if (
            sys.getsizeof(
                json.dumps({**test_dict, **{next_key + batch_size: "a"}})
            )
            > approx_size_bytes
        ):
            break

    return test_dict


@pytest.mark.integration
def test_write_small_message_to_standard_topic(start_service):
    """Test writing a small message to a Kafka topic.

    Setup:
    - A default KafkaDataset is created and initialized as a producer.
    - A small message is generated.

    Expectation: The message is written successfully without raising exceptions.
    """
    dataset: KafkaDataset = AbstractDataset.from_config(
        "test",
        DatasetConfig(
            type="aineko.datasets.kafka.KafkaDataset",
            location="localhost:9092",
            params=None,
        ),
    )
    dataset.create()
    dataset.initialize(
        create="producer", node_name="test_node", pipeline_name="test_pipeline"
    )

    dataset.write(msg={"message": "test"})


@pytest.mark.integration
def test_write_large_message_to_standard_topic(start_service):
    """Test writing a large message to a Kafka topic.

    Setup:
    - A default KafkaDataset is created and initialized as a producer.
    - A message of size ≈2MB is generated.

    Expectation: The write operation raises a KafkaException because the message
    size exceeds the default limit.
    """
    dataset: KafkaDataset = AbstractDataset.from_config(
        "test",
        DatasetConfig(
            type="aineko.datasets.kafka.KafkaDataset",
            location="localhost:9092",
            params=None,
        ),
    )
    dataset.create()
    dataset.initialize(
        create="producer", node_name="test_node", pipeline_name="test_pipeline"
    )

    with pytest.raises(KafkaException) as exc_info:
        dataset.write(msg=generate_dict_of_bytesize(2097152))

    assert "MSG_SIZE_TOO_LARGE" in str(exc_info.value)


@pytest.mark.integration
def test_write_large_message_to_customised_topic(start_service):
    """Test writing a large message to a Kafka topic with custom configuration.

    Setup:
    - A KafkaDataset is created using a parameter to increase the maximum message size to 20MB.
    - A message of size ≈2MB is generated.

    Expectation: The message is written successfully without raising exceptions.
    """
    custom_config = DatasetConfig(
        type="aineko.datasets.kafka.KafkaDataset",
        location="localhost:9092",
        params={"max.message.bytes": 20971520},
    )

    dataset: KafkaDataset = AbstractDataset.from_config("test", custom_config)
    dataset.create()
    dataset.initialize(
        create="producer", node_name="test_node", pipeline_name="test_pipeline"
    )

    dataset.write(msg=generate_dict_of_bytesize(2097152))
