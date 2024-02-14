# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests edge cases to do with kafka clusters."""

import time
from typing import Optional

import pytest
import ray

from aineko import AbstractDataset, AbstractNode, Runner
from aineko.config import DEFAULT_KAFKA_CONFIG
from aineko.datasets.kafka import ConsumerParams


class ConsumerNode(AbstractNode):
    """Node that reads message using different read methods."""

    def _execute(self, params: Optional[dict] = None) -> None:
        """Reads message."""
        self.inputs["messages"].read(how="next", block=False)
        self.inputs["messages"].read(how="last", block=False)
        self.outputs["test_result"].write("OK")
        self.outputs["test_result"].write("END")
        time.sleep(1)
        self.activate_poison_pill()
        return False


@pytest.mark.integration
def test_consume_empty_datasets(start_service):
    """Integration test that checks that empty datasets do not cause errors.

    If a dataset is empty, dataset read methods should not error out.
    """
    runner = Runner(
        pipeline_config_file="tests/conf/integration_test_empty_dataset.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        # This is expected because we activated the poison pill
        pass

    dataset_name = "test_result"
    dataset_config = {
        "type": "aineko.datasets.kafka.KafkaDataset",
        "location": "localhost:9092",
    }
    dataset = AbstractDataset.from_config(dataset_name, dataset_config)
    consumer_params = ConsumerParams(
        **{
            "dataset_name": dataset_name,
            "node_name": "consumer",
            "pipeline_name": "integration_test_kafka_edge_cases",
            "prefix": None,
            "has_pipeline_prefix": True,
            "consumer_config": DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG"),
        }
    )
    dataset.initialize(create_consumer=True, connection_params=consumer_params)
    count_messages = dataset.consume_all(end_message="END")
    assert count_messages[0]["message"] == "OK"
