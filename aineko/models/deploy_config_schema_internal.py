# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for deployment configuration."""

import re
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, field_validator

from aineko.models.validations import check_power_of_2


class MachineConfig(BaseModel, extra="forbid"):
    """Configuration for cloud machine that runs pipelines."""

    type: str
    mem_gib: int
    vcpu: int

    @field_validator("mem_gib")
    @classmethod
    def memory(cls, value: int) -> int:
        """Validates that memory is a power of 2."""
        return check_power_of_2(value)

    @field_validator("vcpu")
    @classmethod
    def power_of_2(cls, value: int) -> int:
        """Validates that vcpu is a power of 2."""
        return check_power_of_2(value)


class ParameterizableDefaults(BaseModel, extra="forbid"):
    """Parameters that can be set in the defaults block."""

    machine_config: Optional[MachineConfig] = None


class GenericPipeline(BaseModel, extra="forbid"):
    """Configuration for a pipeline defined under top-level pipelines key."""

    source: str
    name: Optional[str] = None
    machine_config: Optional[MachineConfig] = None


class LoadBalancer(BaseModel, extra="forbid"):
    """Configuration for a load balancer."""

    pipeline: str
    port: int


class SpecificPipeline(BaseModel, extra="forbid"):
    """Pipeline defined under the top-level environments key."""

    source: Optional[str] = None  # Pipeline config file path
    name: Optional[str] = None  # Pipeline name
    machine_config: Optional[MachineConfig] = None


class FullPipeline(BaseModel, extra="forbid"):
    """Pipeline defined in the full deployment config."""

    source: str
    name: Optional[str] = None
    machine_config: MachineConfig


class Environment(BaseModel, extra="forbid"):
    """Environment defined under the top-level environments key."""

    pipelines: List[Union[str, Dict[str, SpecificPipeline]]]
    load_balancers: Optional[Dict[str, List[LoadBalancer]]] = None

    @field_validator("load_balancers")
    @classmethod
    def validate_lb_endpoint(
        cls, value: Optional[Dict[str, List[LoadBalancer]]]
    ) -> Optional[Dict[str, List[LoadBalancer]]]:
        """Validates Load balancer endpoints.

        The following criteria apply:
            - Endpoints must be 12 characters or fewer.
            - Can only contain alphanumeric characters and hyphens.
        """
        if value is None:
            return value
        for endpoint in value.keys():
            if len(endpoint) > 12:
                raise ValueError(
                    f"Endpoints should be 12 characters or fewer: {endpoint}."
                )
            if re.compile("^[a-zA-Z0-9-]+$").fullmatch(endpoint) is None:
                raise ValueError(
                    "Endpoints can only contain alphanumeric characters "
                    f"and hyphens: {endpoint}."
                )
        return value


class FullEnvironment(BaseModel, extra="forbid"):
    """Environment defined under the top-level environments key."""

    pipelines: List[Union[Dict[str, FullPipeline], str]]
    load_balancers: Optional[Dict[str, List[LoadBalancer]]] = None
