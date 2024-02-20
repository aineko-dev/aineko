# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from typing import Dict, Optional

from pydantic import BaseModel, Field

from aineko.models.dataset_config_schema import DatasetConfig


class Config(BaseModel):
    """Pipeline configuration model.

    Pipeline configurations are defined by the user in a YAML file. This model
    is a representation of a serialized pipeline configuration.
    """

    class Pipeline(BaseModel):
        """Pipeline model."""

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
        datasets: Dict[str, DatasetConfig]

    pipeline: Pipeline
