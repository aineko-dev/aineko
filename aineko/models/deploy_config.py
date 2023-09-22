"""Models for deployment configuration."""

from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from aineko.models.validations import check_power_of_2


class MachineConfig(BaseModel):
    """Configuration for cloud machine that runs pipelines."""

    type: str
    mem: str
    vcpu: int

    @validator("mem")
    def memory(cls, v: str) -> int:  # pylint: disable=no-self-argument
        """Validates that memory is a power of 2 and ends in `Gib`."""
        value = v[:-3]
        mem_value: int = 0
        if v[-3:] != "Gib":
            raise ValueError("Memory value must end in `Gib`")
        if not value.isdigit():
            raise ValueError(f"Memory value {value} must be an integer")
        mem_value = check_power_of_2(int(value))
        return mem_value

    @validator("vcpu")
    def power_of_2(cls, v: int) -> int:  # pylint: disable=no-self-argument
        """Validates that vcpu is a power of 2."""
        value = check_power_of_2(int(v))
        return value


class Pipeline(BaseModel, extra="forbid"):
    """Configuration for a pipeline."""

    source: str
    name: Optional[str]
    machine_config: Optional[MachineConfig]


class Pipelines(BaseModel, extra="forbid"):
    """Configuration for list of pipelines."""

    pipelines: List[Dict[str, Pipeline]]


class DeploymentConfig(BaseModel, extra="forbid"):
    """Configuration for deploy.yml."""

    project: str
    version: str
    defaults: Optional[Dict]
    pipelines: Dict[str, Pipeline]
    environments: Dict[str, Pipelines]

    @validator("version")
    def semver(cls, v: str) -> str:  # pylint: disable=no-self-argument
        """Validates that versioning follow semver convention."""
        if len(v.split(".")) != 3:
            raise ValueError("Version must be in the form `1.2.3`")
        return v
