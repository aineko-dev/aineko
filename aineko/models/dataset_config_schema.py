# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Internal models for the dataset configuration schema."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DatasetConfig(BaseModel):
    """Dataset configuration model."""

    type: str = Field(
        ...,
        description="A dotted path to the dataset class implementation.",
        examples=[
            "aineko.datasets.kafka.KafkaDataset",
            "foo.bar.baz.BazDataset",
        ],
    )
    location: Optional[str] = Field(
        None,
        description=(
            "Location of the dataset storage layer. For example, a kafka "
            "broker address."
        ),
        examples=["localhost:9092"],
    )
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="The initialization parameters for the dataset.",
        examples=[{"param_1": "bar"}],
    )
