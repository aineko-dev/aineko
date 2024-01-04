# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Config model."""

    class Pipeline(BaseModel):
        """Pipeline model."""

        class Dataset(BaseModel):
            """Dataset model."""

            type: str
            params: dict | None = None

        class Node(BaseModel):
            """Node model."""

            class_name: str = Field(..., alias="class")
            node_params: dict | None = None
            node_settings: dict | None = None
            inputs: list | None = None
            outputs: list | None = None

        name: str
        default_node_settings: dict | None
        nodes: dict[str, Node]
        datasets: dict[str, Dataset]

    pipeline: Pipeline
