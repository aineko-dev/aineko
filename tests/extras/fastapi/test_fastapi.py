# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests that a pipeline with the FastAPI app runs correctly."""

import time
from typing import Dict

import pytest
import ray
import requests

from aineko import AbstractDataset, AbstractNode, Runner
from aineko.config import DEFAULT_KAFKA_CONFIG
from aineko.datasets.kafka import ConsumerParams


class FastAPIChecker(AbstractNode):
    """Node that checks that the FastAPI server is running."""

    def _execute(self, params: Dict):
        """Checks that the FastAPI server is running."""
        results = {}

        time.sleep(5)

        response = requests.get("http://localhost:8000/produce")
        results["produce"] = response.status_code

        response = requests.get("http://localhost:8000/next")
        results["next"] = response.json()

        response = requests.get("http://localhost:8000/last")
        results["last"] = response.json()

        response = requests.get("http://localhost:8000/health")
        results["health"] = response.status_code

        self.outputs["test_result"].write(results)

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
                "pipeline_name": "test_fastapi",
                "prefix": None,
                "has_pipeline_prefix": True,
                "consumer_config": DEFAULT_KAFKA_CONFIG.get("CONSUMER_CONFIG"),
            }
        )
        dataset.initialize(
            create_consumer=True, connection_params=consumer_params
        )
        test_results = dataset.next()
        assert test_results["message"]["produce"] == 200
        assert test_results["message"]["next"]["message"] == 1
        assert test_results["message"]["last"]["message"] == 3
        assert test_results["message"]["health"] == 200
