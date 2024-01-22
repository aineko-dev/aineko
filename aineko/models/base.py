# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Base models for Aineko."""
import datetime

from pydantic import BaseModel, Field

from aineko.config import AINEKO_CONFIG


class WrappedMessage(BaseModel):
    """Aineko message wrapper.

    This model is used when consuming and producing messages by nodes. It
    contains the message itself, along with metadata about the message.
    """

    message: dict = Field(..., description="Message payload")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now().strftime(
            AINEKO_CONFIG.get("MSG_TIMESTAMP_FORMAT")
        ),
        description="Message timestamp",
    )
    dataset: str = Field(..., description="Dataset name")
    source_pipeline: str = Field(..., description="Source Pipeline name")
    source_node: str = Field(..., description="Source Node name")
