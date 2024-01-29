# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Schema models for deployment configuration specified in deploy.yml.

DeploymentConfig is the schema for a user written deploy.yml file. This format
is more compact, and allows for defining re-usable config under the `defaults`
and `pipelines` keys.

FullDeploymentConfig is the schema for the full deployment configuration, which
is the machine-readable version of DeploymentConfig. All re-usable config is
explicitly injected into the config so all pipelines are explicitly defined.
This config represents the source of truth for all deployments of aineko
pipelines.
"""

from typing import Dict, Optional

from pydantic import BaseModel, field_validator

from aineko.models.deploy_config_schema_internal import (
    Environment,
    GenericPipeline,
    ParameterizableDefaults,
)


class DeploymentConfig(BaseModel, extra="forbid"):
    """User deployment configuration (Schema for deploy.yml)."""

    version: str
    defaults: Optional[ParameterizableDefaults] = None
    pipelines: Dict[str, GenericPipeline]
    environments: Dict[str, Environment]

    @field_validator("version")
    @classmethod
    def semver(cls, v: str) -> str:
        """Validates that versioning follow semver convention."""
        if len(v.split(".")) != 3:
            raise ValueError("Version must be in the form `1.2.3`")
        return v


class FullDeploymentConfig(BaseModel):
    """Full deployment configuration (Schema for deploy.yml)."""

    version: str
    environments: Dict[str, Environment]

    @field_validator("version")
    @classmethod
    def semver(cls, v: str) -> str:
        """Validates that versioning follow semver convention."""
        if len(v.split(".")) != 3:
            raise ValueError("Version must be in the form `1.2.3`")
        return v
