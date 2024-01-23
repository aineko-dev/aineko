# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that a pipeline with the FastAPI app runs correctly."""

import time

import pytest
import ray
import requests

from aineko import AbstractNode, DatasetConsumer, Runner


class FastAPIChecker(AbstractNode):
    """Node that checks that the FastAPI server is running."""

    def _execute(self, params: dict):
        """Checks that the FastAPI server is running."""
        results = {}

        time.sleep(5)

        response = requests.get("http://localhost:8000/produce")
        results["produce"] = response.status_code

        response = requests.get("http://localhost:8000/next")
        results["next"] = response.json()

        response = requests.get("http://localhost:8000/last")
        results["last"] = response.json()

        self.producers["test_result"].produce(results)

        self.activate_poison_pill()


@pytest.mark.integration
def test_fastapi_node(start_service):
    """Integration test to check that FastAPI node works.

    Spin up a pipeline containing the fastapi node and a FastAPIChecker
    node that queries the api server using the fastapi endpoints.
    The FastAPIChecker node uses the endpoints to produce messages and
    other ones to consume messages.
    """
    runner = Runner(
        pipeline_config_file="tests/extras/fastapi/test_fastapi.yml",
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name="test_result",
            node_name="consumer",
            pipeline_name="test_fastapi",
            dataset_config={},
            has_pipeline_prefix=True,
        )
        test_results = consumer.next()
        assert test_results.message["produce"] == 200
        assert test_results.message["next"]["message"]["value"] == 1
        assert test_results.message["last"]["message"]["value"] == 3
