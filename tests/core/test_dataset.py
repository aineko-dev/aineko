# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the fake datasets inputs and outputs."""
from aineko.datasets.kafka import FakeDatasetInput, FakeDatasetOutput


def test_fake_data_input() -> None:
    """Tests the FakeDataConsumer class."""
    input = FakeDatasetInput(
        dataset_name="test", node_name="test_node", values=[0, 1, 2]
    )
    # Test that the consumer returns the correct values
    for i in range(3):
        assert input.read()["message"] == i
    # Test that consumer returns None when out of values
    assert input.read() is None


def test_fake_data_output() -> None:
    """Tests the FakeDataProducer class."""
    output = FakeDatasetOutput(
        dataset_name="test",
        node_name="test_node",
    )
    for i in range(3):
        output.write(i)
    assert output.values == [0, 1, 2]
