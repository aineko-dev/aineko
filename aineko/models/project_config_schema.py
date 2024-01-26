# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Schema models for project configuration specified in aineko.yml.

These models are used to validate the project configuration specified in
repos that are used in `aineko create`.
"""

from typing import Optional

from pydantic import BaseModel, field_validator

from aineko import __version__


class ProjectConfig(BaseModel):
    """Project configuration (Schema for aineko.yml)."""

    aineko_version: str
    project_name: str
    project_slug: Optional[str] = None
    project_description: Optional[str] = None
    pipeline_slug: Optional[str] = None

    @field_validator("aineko_version")
    @classmethod
    def version(cls, v: str) -> str:
        """Validates that the aineko version matches."""
        if v != __version__:
            raise ValueError(
                f"Project config `aineko.yml` requires version {v}, "
                f"but current version is {__version__}. Use "
                f"`pip install aineko=={v}` to install the correct version."
            )
        return v
