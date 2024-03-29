# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for deploy_config models."""

import pytest
from pydantic import ValidationError

from aineko.models.deploy_config_schema import DeploymentConfig


def test_deployment_config(
    pipeline_config, pipelines_config, load_balancers_config
):
    """Test DeploymentConfig model."""
    deploy = {
        "version": "1.0.0",
        "defaults": {
            "machine_config": {"type": "ec2", "mem_gib": 16, "vcpu": 4},
        },
        "pipelines": {
            "test_pipeline": pipeline_config,
        },
        "environments": {
            "develop": {
                **pipelines_config,
                **load_balancers_config,
            }
        },
    }
    assert DeploymentConfig(**deploy)

    # Fail if extra keys are added
    deploy["extra"] = "extra"
    with pytest.raises(ValidationError):
        DeploymentConfig(**deploy)

    # Fail if load balancers are defined under pipelines
    with pytest.raises(ValidationError):
        deploy = {
            "version": "1.0.0",
            "defaults": {
                "machine_config": {"type": "ec2", "mem_gib": 16, "vcpu": 4},
            },
            "pipelines": {
                "test_pipeline": pipeline_config,
                **load_balancers_config,
            },
            "environments": {
                "develop": {
                    **pipelines_config,
                }
            },
        }
        DeploymentConfig(**deploy)
