# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from aineko.models.dataset_config_schema import DatasetConfig


class NodeSettings(BaseModel):
    """Node settings model.

    This model is used to define settings for a node. The main use case is to
    define the number of CPUs to use for a node. However, it can be extended to
    include all Ray remote parameters as described in the [Ray documentation.](
    https://docs.ray.io/en/latest/ray-core/api/doc/ray.remote.html#ray.remote/)
    {:target="_blank"}
    """

    num_cpus: Optional[float] = Field(
        None,
        description="The number of CPUs to use for a node.",
        gt=0.0,
        examples=[1.0, 0.5],
    )
    model_config = {"extra": "allow"}


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
            node_settings: Optional[NodeSettings] = None
            inputs: Optional[List[str]] = None
            outputs: Optional[List[str]] = None

        name: str
        default_node_settings: Optional[NodeSettings] = None
        nodes: Dict[str, Node]
        datasets: Dict[str, DatasetConfig]

    pipeline: Pipeline
