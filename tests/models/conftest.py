"""Test fixtures for models."""

import pytest


@pytest.fixture(scope="function")
def machine_config():
    return {"type": "ec2", "mem_gib": 16, "vcpu": 4}


@pytest.fixture(scope="function")
def pipeline_config():
    return {
        "source": "./conf/pipeline.yml",
        "name": "test",
    }


@pytest.fixture(scope="function")
def pipelines_config(pipeline_config, machine_config):
    return {
        "pipelines": [
            {"test_pipeline_1": pipeline_config},
            {
                "test_pipeline_2": {
                    **pipeline_config,
                    **{"machine_config": machine_config},
                }
            },
        ]
    }
