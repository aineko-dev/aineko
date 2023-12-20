# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests edge cases to do with kafka clusters."""

import time
from typing import Optional

import ray

from aineko import AbstractNode, DatasetConsumer, Runner


class ConsumerNode(AbstractNode):
    """Node that consumes message using different consume methods."""

    def _execute(self, params: Optional[dict] = None) -> None:
        """Consumes message."""
        self.consumers["messages"].consume(how="next")
        self.consumers["messages"].consume(how="last", timeout=1)
        self.producers["test_result"].produce("OK")
        self.producers["test_result"].produce("END")
        time.sleep(1)
        self.activate_poison_pill()
        return False


def test_consume_empty_datasets():
    """Integration test that checks that empty datasets do not cause errors.

    If a dataset is empty, dataset consumer methods should not error out.
    """
    runner = Runner(
        pipeline_config_file="tests/conf/integration_test_empty_dataset.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="test_result",
            node_name="consumer",
            pipeline_name="integration_test_kafka_edge_cases",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        count_messages = consumer.consume_all(end_message="END")
        assert count_messages[0]["message"] == "OK"
