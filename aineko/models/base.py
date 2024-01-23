# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Base models for Aineko."""
import datetime
from typing import Union

from pydantic import BaseModel, Field

from aineko.config import AINEKO_CONFIG


class MessageData(BaseModel):
    """Aineko message data model.

    The `MessageData` is a Pydantic model that represents the data as produced
    or consumed by the nodes in an Aineko pipeline. It contains the message
    itself, along with metadata about the message.
    """

    message: Union[dict, str] = Field(..., description="Message payload")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now().strftime(
            AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
        ),
        description="Message timestamp",
    )
    dataset: str = Field(..., description="Dataset name")
    source_pipeline: str = Field(..., description="Source Pipeline name")
    source_node: str = Field(..., description="Source Node name")
