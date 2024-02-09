# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that a pipeline with the HTTPPoller runs correctly."""
import time
from typing import Dict, Optional

import pytest
import ray

from aineko import AbstractNode, DatasetConsumer, Runner


class HTTPPollerChecker(AbstractNode):
    """Node that checks that the HTTPPoller is running."""

    def _execute(self, params: Dict):
        """Checks that the HTTPPoller is running."""
        results = {}
        for msg_num in range(5):
            test_message = self.consumers["test_messages"].next()
            results[f"message_{msg_num}"] = test_message["message"]
        self.producers["test_result"].produce(results)
        self.activate_poison_pill()
        time.sleep(5)


@pytest.mark.integration
def test_http_poller_node(start_service):
    """Integration test to check that HTTPPoller node works.

    Spin up a pipeline containing the HTTPPoller node and a FastAPI node that
    creates a test an API server. The HTTPPoller node connects to the server,
    sends requests for data, and produces results to the test_messages dataset.
    """
    runner = Runner(
        pipeline_config_file="tests/extras/connectors/test_http_poller.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="test_result",
            node_name="consumer",
            pipeline_name="test_http_poller",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        test_results = consumer.next()
        assert test_results["message"] == {
            "message_0": "Hello World!",
            "message_1": "Hello World!",
            "message_2": "Hello World!",
            "message_3": "Hello World!",
            "message_4": "Hello World!",
        }
