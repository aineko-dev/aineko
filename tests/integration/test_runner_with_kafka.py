"""Tests that runner is able to generate a pipeline that works
with a kafka zookeeper and broker service available.
"""

import time
from typing import Optional

import ray

from aineko.core.dataset import DatasetConsumer
from aineko.core.node import AbstractNode
from aineko.core.runner import Runner


class IntegerWriter(AbstractNode):
    """Node that counts integers every second."""

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        self.limit = 10
        self.counter = 0

    def _execute(self, params: Optional[dict] = None) -> None:
        """Counts integers every second."""
        if self.counter < self.limit:
            self.producers["count"].produce(self.counter)
            self.counter += 1
            time.sleep(0.1)
        else:
            self.producers["count"].produce("END")
            return False

    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        """Activate the poison pill upon execute completion."""
        time.sleep(1)
        self.activate_poison_pill()


def test_write_to_kafka():
    """Integration test to check that nodes can write to kafka.

    First set up the integration test pipeline run it, making use
    of the poison pill function take down the pipeline once
    all messages are sent.

    Next, create a consumer to read all messages directly from the
    kafka topic and check that the messages match what was sent.
    """
    runner = Runner(
        pipeline="integration_test",
        pipeline_config_file="tests/conf/integration_test.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="count",
            node_name="consumer",
            pipeline_name="integration_test",
            dataset_config={},
        )
        count_messages = consumer.consume_all(end_message="END")
        count_values = [msg["message"] for msg in count_messages]
        assert count_values == list(range(10))
