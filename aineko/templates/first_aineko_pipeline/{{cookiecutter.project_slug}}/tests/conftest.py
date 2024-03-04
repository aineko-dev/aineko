# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test fixtures for {{cookiecutter.project_slug}}."""
from typing import Any, Dict, List, Union

import pytest


@pytest.fixture
def message_helper():
    """Fixture to help with output message validation."""

    def _message_helper(
        messages: Union[List[Dict], Dict]
    ) -> Union[List[Any], Any]:
        """Helper method to return the message payload from a list of messages.

        Example usage:
            ```python
            messages = [
                    {
                        "message": 1,
                        "source_node": "foo",
                        "source_pipeline": "bar",
                    },
                    {
                        "message": 2,
                        "source_node": "foo",
                        "source_pipeline": "bar",
                    },
                    {
                        "message": 3,
                        "source_node": "foo",
                        "source_pipeline": "bar",
                    },
            ]
            message_helper(messages)
            # Returns: [1, 2, 3]
            ```

        Args:
            messages: List of messages or a single message

        Returns:
            List of message payloads or a single message payload
        """
        if isinstance(messages, dict):
            return messages["message"]

        return [message["message"] for message in messages]

    return _message_helper
