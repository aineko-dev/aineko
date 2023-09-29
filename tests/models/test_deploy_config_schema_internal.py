# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for aineko.models.deploy_config_internal.py."""

import pytest
from pydantic import ValidationError

from aineko.models.deploy_config_schema_internal import (
    Environment,
    MachineConfig,
    SpecificPipeline,
)


def test_machine_config(machine_config):
    """Test MachineConfig model."""
    expected = {"type": "ec2", "mem_gib": 16, "vcpu": 4}
    assert MachineConfig(**machine_config) == expected

    with pytest.raises(ValueError):
        MachineConfig(**{"type": "ec2", "mem_gib": 16, "vcpu": 5})


def test_pipeline(pipeline_config, machine_config):
    """Test Pipeline model."""
    # Only source
    assert SpecificPipeline(source="./conf/pipeline.yml")
    # Source and name
    assert SpecificPipeline(**pipeline_config)
    # Source, name, and machine_config
    assert SpecificPipeline(
        **pipeline_config, **{"machine_config": machine_config}
    )

    # Fail if extra keys are added
    pipeline_config["extra"] = "extra"
    with pytest.raises(ValidationError):
        SpecificPipeline(**pipeline_config)


def test_environments(pipelines_config):
    """Test Pipelines model."""
    assert Environment(**pipelines_config)
