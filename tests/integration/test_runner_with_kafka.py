# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that runner is able to generate a pipeline that works
with a kafka zookeeper and broker service available.
"""
import time
from typing import Optional

import pytest
import ray
from click.testing import CliRunner

from aineko.__main__ import cli
from aineko.core.dataset import DatasetConsumer
from aineko.core.node import AbstractNode
from aineko.core.runner import Runner

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
            self.producers["messages"].produce(self.messages.pop(0))
            time.sleep(0.1)
        else:
            self.producers["messages"].produce("END")
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
        msg = self.consumers["messages"].consume()
        if time.time() - self.last_updated > self.timeout:
            print(f"Received messages: {self.received}")
            print(self.consumers["messages"].topic_name)
            raise TimeoutError("Timed out waiting for messages.")

        if not msg:
            return

        if msg["message"] == "END":
            return False

        self.received.append(msg["message"])
        self.last_updated = time.time()

    def _post_loop_hook(self, params: dict | None = None) -> None:
        if self.messages != self.received:
            raise ValueError(
                "Failed to read expected messages."
                f"Expected: {self.messages}, Received: {self.received}"
            )
        self.producers["test_result"].produce("TEST PASSED")
        self.producers["test_result"].produce("END")
        self.activate_poison_pill()


@pytest.mark.integration
def test_write_read_to_kafka():
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
    runner = CliRunner()
    result = runner.invoke(cli, ["service", "restart"])
    assert result.exit_code == 0

    runner = Runner(
        pipeline_config_file="tests/conf/integration_test_write.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="messages",
            node_name="consumer",
            pipeline_name="integration_test_write",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        count_messages = consumer.consume_all(end_message="END")
        count_values = [msg["message"] for msg in count_messages]
        assert count_values == MESSAGES

    runner = Runner(
        pipeline_config_file="tests/conf/integration_test_read.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="test_result",
            node_name="consumer",
            pipeline_name="integration_test_read",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        count_messages = consumer.consume_all(end_message="END")
        assert count_messages[0]["source_pipeline"] == "integration_test_read"
        assert count_messages[0]["message"] == "TEST PASSED"
