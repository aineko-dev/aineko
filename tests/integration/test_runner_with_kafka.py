# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that runner is able to generate a pipeline that works
with a kafka zookeeper and broker service available.
"""
import time
from typing import Optional

import pytest
import ray

from aineko import AbstractDataset, AbstractNode, Runner
from aineko.config import DEFAULT_KAFKA_CONFIG
from aineko.datasets.kafka import ConsumerParams

MESSAGES = [
    0,
    1,
    2,
    3,  # int
    "test_1",
    "test_2",  # str
    {"test_1": 1, "test_2": 2},  # dict
]


class MessageWriter(AbstractNode):
    """Node that produces messages every 0.1 second."""

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        self.messages = MESSAGES

    def _execute(self, params: Optional[dict] = None) -> None:
        """Sends message."""
        if len(self.messages) > 0:
            self.outputs["messages"].write(self.messages.pop(0))
            time.sleep(0.1)
        else:
            self.outputs["messages"].write("END")
            return False

    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        """Activate the poison pill upon execute completion."""
        time.sleep(1)
        self.activate_poison_pill()


class MessageReader(AbstractNode):
    """Node that reads messages and logs them."""

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        self.messages = MESSAGES
        self.received = []
        self.timeout = 20  # seconds to wait for before terminating
        self.last_updated = time.time()

    def _execute(self, params: Optional[dict] = None) -> None:
        """Read message"""
        msg = self.inputs["messages"].next()
        if time.time() - self.last_updated > self.timeout:
            print(f"Received messages: {self.received}")
            print(self.inputs["messages"].topic_name)
            raise TimeoutError("Timed out waiting for messages.")

        if not msg:
            return

        if msg["message"] == "END":
            return False

        self.received.append(msg["message"])
        self.last_updated = time.time()

    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        if self.messages != self.received:
            raise ValueError(
                "Failed to read expected messages."
                f"Expected: {self.messages}, Received: {self.received}"
            )
        self.outputs["test_result"].write("TEST PASSED")
        self.outputs["test_result"].write("END")
        self.activate_poison_pill()


@pytest.mark.integration
def test_write_read_to_kafka(start_service, subtests):
    """Integration test to check that nodes can write to kafka.

    First set up the integration test pipeline run it, making use
    of the poison pill function take down the pipeline once
    all messages are sent.

    Next, create a consumer to read all messages directly from the
    kafka topic and check that the messages match what was sent.

    Then test node reading functionality by setting up a new pipeline
    that reads from the created dataset and checks that the messages
    are as expected.
    """
    with subtests.test("Test writing to Kafka."):
        runner = Runner(
            pipeline_config_file="tests/conf/integration_test_write.yml",
        )
        try:
            runner.run()
        except ray.exceptions.RayActorError:
            dataset_name = "messages"
            dataset_config = {
                "type": "aineko.datasets.kafka.Kafka",
                "location": "localhost:9092",
            }
            dataset = AbstractDataset.from_config(dataset_name, dataset_config)
            consumer_params = ConsumerParams(
                **{
                    "dataset_name": dataset_name,
                    "node_name": "consumer",
                    "pipeline_name": "integration_test_write",
                    "prefix": None,
                    "has_pipeline_prefix": True,
                    "consumer_config": DEFAULT_KAFKA_CONFIG.get(
                        "CONSUMER_CONFIG"
                    ),
                }
            )
            dataset.initialize(
                create_consumer=True, connection_params=consumer_params
            )
            count_messages = dataset.consume_all(end_message="END")
            count_values = [msg["message"] for msg in count_messages]
            assert count_values == MESSAGES

    with subtests.test("Test reading from Kafka"):
        runner = Runner(
            pipeline_config_file="tests/conf/integration_test_read.yml",
        )
        try:
            runner.run()
        except ray.exceptions.RayActorError:
            dataset_name = "test_result"
            dataset_config = {
                "type": "aineko.datasets.kafka.Kafka",
                "location": "localhost:9092",
            }
            dataset = AbstractDataset.from_config(dataset_name, dataset_config)
            consumer_params = ConsumerParams(
                **{
                    "dataset_name": dataset_name,
                    "node_name": "consumer",
                    "pipeline_name": "integration_test_read",
                    "prefix": None,
                    "has_pipeline_prefix": True,
                    "consumer_config": DEFAULT_KAFKA_CONFIG.get(
                        "CONSUMER_CONFIG"
                    ),
                }
            )
            dataset.initialize(
                create_consumer=True, connection_params=consumer_params
            )
            count_messages = dataset.consume_all(end_message="END")
            print("count_messages are...")
            print(count_messages)
            print("...")
            # assert count_messages[0]["source_pipeline"] == "integration_test_read"
            assert count_messages[0]["message"] == "TEST PASSED"

    with subtests.test("Test the consume.last functionality"):
        # Test consume.last functionality
        last_message = dataset.last(timeout=10)
        assert last_message["message"] == "END"
