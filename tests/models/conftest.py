# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test fixtures for models."""

import pytest

from aineko.utils.io import load_yaml


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


@pytest.fixture(scope="function")
def load_balancer_config():
    return {
        "pipeline": "test_pipeline_1",
        "port": 8080,
    }


@pytest.fixture(scope="function")
def load_balancers_config(load_balancer_config):
    return {"load_balancers": {"test-point": [load_balancer_config]}}


@pytest.fixture(scope="function")
def node_log_to_dataset():
    return load_yaml("tests/conf/node_log_to_dataset.yml")


@pytest.fixture(scope="function")
def pipeline_log_to_dataset():
    return load_yaml("tests/conf/pipeline_log_to_dataset.yml")


@pytest.fixture(scope="function")
def pipeline_dont_log_to_dataset():
    return load_yaml("tests/conf/pipeline_dont_log_to_dataset.yml")


@pytest.fixture(scope="function")
def invalid_pipeline_log_to_dataset():
    return load_yaml("tests/conf/invalid_pipeline_log_to_dataset.yml")


@pytest.fixture(scope="function")
def invalid_node_log_to_dataset():
    return load_yaml("tests/conf/invalid_node_log_to_dataset.yml")
