# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from typing import Optional

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Config model."""

    class Pipeline(BaseModel):
        """Pipeline model."""

        class Dataset(BaseModel):
            """Dataset model."""

            type: str
            params: Optional[dict]

        class Node(BaseModel):
            """Node model."""

            class_name: str = Field(..., alias="class")
            node_params: Optional[dict]
            node_settings: Optional[dict]
            inputs: Optional[list]
            outputs: Optional[list]

        name: str
        default_node_settings: Optional[dict]
        nodes: dict[str, Node]
        datasets: dict[str, Dataset]

    pipeline: Pipeline
