"""Tests for deploy_config models."""

import pytest
from pydantic import ValidationError

from aineko.models.deploy_config import (
    DeploymentConfig,
    MachineConfig,
    Pipeline,
    Pipelines,
)


@pytest.fixture(scope="function")
def machine_config():
    return {"type": "ec2", "mem": "16Gib", "vcpu": 4}


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


def test_machine_config(machine_config):
    """Test MachineConfig model."""
    expected = {"type": "ec2", "mem": 16, "vcpu": 4}
    assert MachineConfig(**machine_config) == expected

    with pytest.raises(ValueError):
        MachineConfig(**{"type": "ec2", "mem": "16Gib", "vcpu": 5})


def test_pipeline(pipeline_config, machine_config):
    """Test Pipeline model."""
    # Only source
    assert Pipeline(source="./conf/pipeline.yml")
    # Source and name
    assert Pipeline(**pipeline_config)
    # Source, name, and machine_config
    assert Pipeline(**pipeline_config, **{"machine_config": machine_config})

    # Fail if extra keys are added
    pipeline_config["extra"] = "extra"
    with pytest.raises(ValidationError):
        Pipeline(**pipeline_config)


def test_pipelines(pipelines_config):
    """Test Pipelines model."""
    assert Pipelines(**pipelines_config)


def test_deployment_config(pipeline_config, pipelines_config):
    """Test DeploymentConfig model."""
    deploy = {
        "project": "test_project",
        "version": "1.0.0",
        "defaults": {
            "machine_config": {"type": "ec2", "mem": "16Gib", "vcpu": 4},
            "env_vars": {"key": "value"},
        },
        "pipelines": {
            "test_pipeline": pipeline_config,
        },
        "environments": {"develop": pipelines_config},
    }
    assert DeploymentConfig(**deploy)

    # Fail if extra keys are added
    deploy["extra"] = "extra"
    with pytest.raises(ValidationError):
        DeploymentConfig(**deploy)
