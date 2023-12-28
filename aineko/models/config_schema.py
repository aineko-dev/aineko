# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for pipeline config validation."""
from typing import Optional

from pydantic import BaseModel, Field, model_validator


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
            log_to_dataset: Optional[bool] = None
            logging_namespace: Optional[str] = None

        name: str
        default_node_settings: Optional[dict]
        nodes: dict[str, Node]
        datasets: dict[str, Dataset]
        log_to_dataset: Optional[bool] = None
        logging_namespace: Optional[str] = None

    pipeline: Pipeline

    @model_validator(mode="after")
    def validate_logging_parameters(self) -> "Config":
        """Validate logging parameters.

        This method validates the logging parameters on the pipeline level and
        the node level. It also sets the default values for the logging
        parameters on the node level if they are not specified.
        """
        if not self.pipeline.log_to_dataset and self.pipeline.logging_namespace:
            raise ValueError(
                "logging_namespace must not be specified if log_to_dataset is"
                " falsy."
            )
        for node in self.pipeline.nodes.values():
            if not node.log_to_dataset and node.logging_namespace:
                raise ValueError(
                    "logging_namespace must not be specified if log_to_dataset"
                    " is falsy."
                )

        if self.pipeline.log_to_dataset is True:
            for node in self.pipeline.nodes.values():
                if node.log_to_dataset is None:
                    node.log_to_dataset = True
            if self.pipeline.logging_namespace is not None:
                for node in self.pipeline.nodes.values():
                    if node.logging_namespace is None:
                        node.logging_namespace = self.pipeline.logging_namespace

        elif self.pipeline.log_to_dataset is False:
            for node in self.pipeline.nodes.values():
                if node.log_to_dataset is None:
                    node.log_to_dataset = False
        return self
