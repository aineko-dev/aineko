# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the aineko.core.dataset module."""
from aineko import FakeDatasetConsumer, FakeDatasetProducer


def test_fake_data_consumer() -> None:
    """Tests the FakeDataConsumer class."""
    consumer = FakeDatasetConsumer(
        dataset_name="test", node_name="test_node", values=[0, 1, 2]
    )
    # Test that the consumer returns the correct values
    for i in range(3):
        assert consumer.consume()["message"] == i
    # Test that consumer returns None when out of values
    assert consumer.consume() is None


def test_fake_data_producer() -> None:
    """Tests the FakeDataProducer class."""
    producer = FakeDatasetProducer(
        dataset_name="test",
        node_name="test_node",
    )
    for i in range(3):
        producer.produce(i)
    assert producer.values == [0, 1, 2]
