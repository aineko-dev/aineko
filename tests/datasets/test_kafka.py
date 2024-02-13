# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the fake datasets inputs and outputs."""
from aineko.datasets.kafka import FakeKafka


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
