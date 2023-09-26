# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for deployment configuration."""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator

from aineko.models.validations import check_power_of_2


class MachineConfig(BaseModel, extra="forbid"):
    """Configuration for cloud machine that runs pipelines."""

    type: str
    mem_gib: int
    vcpu: int

    @validator("mem_gib")
    def memory(cls, value: int) -> int:  # pylint: disable=no-self-argument
        """Validates that memory is a power of 2."""
        return check_power_of_2(value)

    @validator("vcpu")
    def power_of_2(cls, value: int) -> int:  # pylint: disable=no-self-argument
        """Validates that vcpu is a power of 2."""
        return check_power_of_2(value)


class ParameterizableDefaults(BaseModel, extra="forbid"):
    """Parameters that can be set in the defaults block."""

    machine_config: Optional[MachineConfig]
    env_vars: Optional[Dict[str, str]]


class GenericPipeline(BaseModel, extra="forbid"):
    """Configuration for a pipeline defined under top-level pipelines key."""

    source: str
    name: Optional[str]
    machine_config: Optional[MachineConfig]
    env_vars: Optional[Dict[str, str]]


class LoadBalancer(BaseModel, extra="forbid"):
    """Configuration for a load balancer."""

    hostname: str
    port: int


class SpecificPipeline(BaseModel, extra="forbid"):
    """Pipeline defined under the top-level environments key."""

    source: Optional[str]  # Pipeline config file path
    name: Optional[str]  # Pipeline name
    machine_config: Optional[MachineConfig]
    env_vars: Optional[Dict[str, str]]
    load_balancers: Optional[List[LoadBalancer]]


class FullPipeline(BaseModel, extra="forbid"):
    """Pipeline defined in the full deployment config."""

    source: str
    name: Optional[str]
    machine_config: MachineConfig
    env_vars: Optional[Dict[str, str]]
    load_balancers: Optional[List[LoadBalancer]]


class Pipelines(BaseModel, extra="forbid"):
    """List of pipelines, under the top-level environments key."""

    pipelines: List[Union[str, Dict[str, SpecificPipeline]]]


class FullPipelines(BaseModel, extra="forbid"):
    """List of complete pipelines, under the top-level environments key."""

    pipelines: List[Dict[str, FullPipeline]]
