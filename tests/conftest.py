# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Aineko test fixtures."""
import datetime
import os
import time
from typing import Any, Dict, List, Optional, Union

import pytest
from click.testing import CliRunner

from aineko import AbstractNode, ConfigLoader, Runner
from aineko.__main__ import cli


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


@pytest.fixture(scope="module")
def conf_directory():
    """Config directory fixture.

    Returns:
        str: Path to config directory
    """
    return os.path.join(os.path.dirname(__file__), "conf")


@pytest.fixture(scope="module")
def test_pipeline_config_file(conf_directory: str):
    """Pipeline config file fixture.

    Returns:
        str: Path to pipeline config file
    """
    return os.path.join(conf_directory, "test_pipeline.yml")


@pytest.fixture(scope="module")
def test_invalid_pipeline_config_file(conf_directory: str):
    """Pipeline config file fixture.

    Returns:
        str: Path to pipeline config file
    """
    return os.path.join(conf_directory, "test_invalid_pipeline.yml")


@pytest.fixture(scope="module")
def config_loader(test_pipeline_config_file: str):
    """Config loader fixture.

    Returns:
        ConfigLoader: Test config loader
    """
    return ConfigLoader(
        pipeline_config_file=test_pipeline_config_file,
    )


@pytest.fixture(scope="module")
def runner(test_pipeline_config_file: str):
    """Runner fixture.

    Returns:
        Runner: Test runner
    """
    return Runner(pipeline_config_file=test_pipeline_config_file)


@pytest.fixture(scope="module")
def dummy_node():
    """Creates dummy node."""

    class DummyNode(AbstractNode):
        """Dummy node that passes through messages."""

        def _execute(self, params: Optional[dict] = None) -> Optional[bool]:
            """Reads message from input and writes it to output."""
            msg = self.inputs["input"].read(how="next", timeout=0)
            if msg is None:
                return False
            self.outputs["output"].write(msg["message"])

    return DummyNode


@pytest.fixture(scope="function")
def start_service():
    runner = CliRunner()
    result = runner.invoke(cli, ["service", "restart", "--hard"])
    assert result.exit_code == 0
    yield
    result = runner.invoke(cli, ["service", "down"])


# Test nodes.


@pytest.fixture(scope="function")
def test_sequencer_node():
    """Returns a sample sequencer node."""

    class TestSequencer(AbstractNode):
        """Test sequencer node."""

        def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
            """Pre loop hook."""
            self.cur_integer = int(params.get("start_int", 0))
            self.num_messages = 0
            self.log(f"Starting at {self.cur_integer}", level="info")

        def _execute(self, params: Optional[dict] = None) -> None:
            """Generates a sequence of integers and writes them to a dataset.

            Args:
                params: Parameters for the node
            """
            # Break if duration has been exceeded
            if self.num_messages >= params.get("num_messages", 25):
                return False

            # Write message to outputs
            self.outputs["integer_sequence"].write(self.cur_integer)
            self.log(f"Produced {self.cur_integer}", level="info")
            self.log("Just a red herring", level="error")
            self.num_messages += 1

            # Increment integer and sleep
            self.cur_integer += 1
            time.sleep(params.get("sleep_time", 1))

    return TestSequencer


@pytest.fixture(scope="function")
def test_doubler_node():
    """Returns a sample doubler node."""

    class TestDoubler(AbstractNode):
        """Test doubler node."""

        def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
            """Initializes node with current time.

            Args:
                params: Defaults to None.
            """
            self.cur_time = time.time()
            self.cur_integer = 0

        def _execute(self, params: Optional[dict] = None) -> None:
            """Generates a sequence of integers and writes them to a dataset.

            Args:
                params: Parameters for the node
            """
            # Break if duration has been exceeded
            if time.time() - self.cur_time > params.get("duration", 30):
                return False

            # Read message from inputs
            message = self.inputs["integer_sequence"].next()

            print(message)

            # Calculate latency
            latency = (
                time.time()
                - datetime.datetime.strptime(
                    message["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                ).timestamp()
            )

            # Log message
            self.log(
                f"Consumed: {message} - "
                f"Latency (ms): {round(latency*1000, 2)}",
                level="info",
            )

            # Convert message to integer
            message = int(message["message"])
            self.cur_integer = message

            # Write message to outputs
            self.outputs["integer_doubles"].write(message * 2)
            self.log(f"Produced {message * 2}", level="info")

    return TestDoubler


@pytest.fixture(scope="module")
def test_internal_value_setter_node():
    """Returns a node that sets the current input as an internal value."""

    class TestInternalValueSetter(AbstractNode):
        """Test sequencer node."""

        def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
            """Pre loop hook."""
            self.cur_integer = 0
            self.num_messages = 0

        def _execute(self, params: Optional[dict] = None) -> None:
            """Reads message from input and sets content to internal value."""

            # Read message from inputs
            cur_integer = self.inputs["integer_sequence"].read(
                how="next", timeout=0
            )
            # Validate message
            if cur_integer is None:
                return

            # Convert message to integer
            cur_integer = int(cur_integer["message"])
            self.cur_integer = cur_integer

    return TestInternalValueSetter
