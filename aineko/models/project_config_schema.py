# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Schema models for project configuration specified in aineko.yml.

These models are used to validate the project configuration specified in
repos that are used in `aineko create`.
"""
from pydantic import BaseModel, field_validator

from aineko import __version__


class ProjectConfig(BaseModel):
    """Project configuration (Schema for aineko.yml)."""

    aineko_version: str
    project_name: str
    project_slug: str | None = None
    project_description: str | None = None
    pipeline_slug: str | None = None

    @field_validator("aineko_version")
    def version(cls, v: str) -> str:  # pylint: disable=no-self-argument
        """Validates that the aineko version matches."""
        if v != __version__:
            raise ValueError(
                f"Project config `aineko.yml` requires version {v}, "
                f"but current version is {__version__}. Use "
                f"`pip install aineko=={v}` to install the correct version."
            )
        return v
