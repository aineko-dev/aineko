# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from typing import Dict, Optional

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Config model."""

    class Pipeline(BaseModel):
        """Pipeline model."""

        class Dataset(BaseModel):
            """Dataset model."""

            type: str
            params: Optional[dict] = None

        class Node(BaseModel):
            """Node model."""

            class_name: str = Field(..., alias="class")
            node_params: Optional[dict] = None
            node_settings: Optional[dict] = None
            inputs: Optional[list] = None
            outputs: Optional[list] = None

        name: str
        default_node_settings: Optional[dict] = None
        nodes: Dict[str, Node]
        datasets: Dict[str, Dataset]

    pipeline: Pipeline
