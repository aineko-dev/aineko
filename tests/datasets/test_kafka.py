# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the fake datasets inputs and outputs."""
import os

from aineko.datasets.kafka import FakeKafka, Kafka


def test_fake_kafka_input() -> None:
    """Tests the FakeKafka class reading."""
    input = FakeKafka(
        dataset_name="test", node_name="test_node", input_values=[0, 1, 2]
    )
    # Test that the input reader returns the correct values
    for i in range(3):
        assert input.read()["message"] == i
    # Test that input reader returns None when out of values
    assert input.read() is None


def test_fake_kafka_output() -> None:
    """Tests the FakeKafka class writing."""
    output = FakeKafka(
        dataset_name="test",
        node_name="test_node",
    )
    for i in range(3):
        output.write(i)
    assert output.output_values == [0, 1, 2]


def test_update_location(subtests) -> None:
    """Tests the update_location method."""
    with subtests.test("Check that the location uses default value."):
        dataset = Kafka("test", {})
        assert dataset.location == "localhost:9092"

    os.environ["KAFKA_CONFIG_BOOTSTRAP_SERVERS"] = "localhost:5678"

    with subtests.test("Check that the location uses value from config first."):
        dataset = Kafka("test", {"location": "localhost:1234"})
        dataset._admin_client = None
        assert dataset.location == "localhost:1234"

    with subtests.test(
        "Check that the location uses value from environment second."
    ):
        dataset = Kafka("test", {})
        dataset._admin_client = None
        assert dataset.location == "localhost:5678"
