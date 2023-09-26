"""Models for deployment configuration."""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator

from aineko.models.validations import check_power_of_2


class MachineConfig(BaseModel, extra="forbid"):
    """Configuration for cloud machine that runs pipelines."""

    type: str
    mem: int
    vcpu: int

    @validator("mem", pre=True)
    def memory(  # pylint: disable=no-self-argument
        cls, v: Union[str, int]
    ) -> int:
        """Validates that memory is a power of 2 and ends in `Gib` if str."""
        value: Union[str, int]
        if isinstance(v, str):
            value = v[:-3]
            if v[-3:] != "Gib":
                raise ValueError("Memory value must end in `Gib`")
            if not value.isdigit():
                raise ValueError(f"Memory value {value} must be an integer")
        else:
            value = v
        mem_value: int = 0
        mem_value = check_power_of_2(int(value))
        return mem_value

    @validator("vcpu")
    def power_of_2(cls, v: int) -> int:  # pylint: disable=no-self-argument
        """Validates that vcpu is a power of 2."""
        value = check_power_of_2(int(v))
        return value


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

    source: Optional[str]
    name: Optional[str]
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


class DeploymentConfig(BaseModel, extra="forbid"):
    """Configuration for deploy.yml."""

    project: str
    version: str
    defaults: Optional[ParameterizableDefaults]
    pipelines: Dict[str, GenericPipeline]
    environments: Dict[str, Pipelines]

    @validator("version")
    def semver(cls, v: str) -> str:  # pylint: disable=no-self-argument
        """Validates that versioning follow semver convention."""
        if len(v.split(".")) != 3:
            raise ValueError("Version must be in the form `1.2.3`")
        return v


class FullDeploymentConfig(BaseModel):
    """Full deployment configuration."""

    project: str
    version: str
    environments: Dict[str, FullPipelines]

    @validator("version")
    def semver(cls, v: str) -> str:  # pylint: disable=no-self-argument
        """Validates that versioning follow semver convention."""
        if len(v.split(".")) != 3:
            raise ValueError("Version must be in the form `1.2.3`")
        return v
