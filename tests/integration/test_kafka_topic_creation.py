# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for Dataset write operations."""

import json
import sys
import time
import traceback
from typing import Optional

import pytest
import ray

from aineko import AbstractNode, Runner


def generate_dict_of_bytesize(approx_size_bytes: int) -> dict:
    """Generate a dict of a given size in bytes when produced as a message.

    This function can be used to generate a dictionary with a size close to the
    desired size when serialized as a JSON message. This is useful for testing
    the maximum message size that can be written to a Kafka topic.

    Args:
        approx_size_bytes: The approximate size in bytes of the message.

    Returns:
        The dictionary with a size close to the desired size.
    """
    test_dict = {}
    batch_size = 10000  # Adjust based on precision-speed tradeoff

    # Initialize an empty JSON string representation of the dictionary
    json_str = json.dumps(test_dict)

    while sys.getsizeof(json_str) < approx_size_bytes:
        next_key = len(test_dict)
        for i in range(batch_size):
            test_dict[next_key + i] = "a"  # Populate with dummy data

        # Update the JSON string representation after adding the batch
        json_str = json.dumps(test_dict)

        # Check if the next addition will exceed the desired size
        if (
            sys.getsizeof(
                json.dumps({**test_dict, **{next_key + batch_size: "a"}})
            )
            > approx_size_bytes
        ):
            break

    return test_dict


class CustomMessageWriter(AbstractNode):
    def _execute(self, params: Optional[dict] = None) -> None:
        """Sends message."""
        self.producers["message_dataset"].produce(
            generate_dict_of_bytesize(params["message_size"])
        )

        return False

    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        """Activate the poison pill upon execute completion."""
        time.sleep(1)
        self.activate_poison_pill()


@pytest.mark.integration
def test_write_small_message_to_standard_topic(start_service, tmp_path):
    """Test writing a small message to a standard Kafka topic.

    Setup:
    - A default dataset is created.
    - A small message is generated.

    Expectation: The message is written successfully without raising exceptions.
    """
    custom_yaml = """
pipeline:
  name: integration_test_write

  default_node_settings:
    num_cpus: 0.5

  nodes:
    sequence:
      class: tests.integration.test_kafka_topic_creation.CustomMessageWriter
      node_params:
        message_size: 1024
      outputs:
        - message_dataset

  datasets:
    message_dataset:
      type: kafka_stream
    """
    custom_yaml_file = tmp_path / "custom_pipeline_config.yml"
    custom_yaml_file.write_text(custom_yaml)

    stack_trace = ""
    runner = Runner(pipeline_config_file=custom_yaml_file)
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        # This is expected because we activated the poison pill
        stack_trace = traceback.format_exc()
        pass

    assert "MSG_SIZE_TOO_LARGE" not in stack_trace


@pytest.mark.integration
def test_write_large_message_to_standard_topic(start_service, tmp_path):
    """Test writing a large message to a standard Kafka topic.

    Setup:
    - A default dataset is created.
    - A message of size ≈2MB is generated.

    Expectation: The write operation raises a KafkaException because the message
    size exceeds the default limit.
    """

    custom_yaml = """
pipeline:
  name: integration_test_write

  default_node_settings:
    num_cpus: 0.5

  nodes:
    sequence:
      class: tests.integration.test_kafka_topic_creation.CustomMessageWriter
      node_params:
        message_size: 2097152
      outputs:
        - message_dataset

  datasets:
    message_dataset:
      type: kafka_stream
    """
    custom_yaml_file = tmp_path / "custom_pipeline_config.yml"
    custom_yaml_file.write_text(custom_yaml)

    stack_trace = ""
    runner = Runner(pipeline_config_file=custom_yaml_file)

    try:
        runner.run()
    except ray.exceptions.RayActorError:
        # This is expected because we activated the poison pill
        stack_trace = traceback.format_exc()
        pass

    assert "MSG_SIZE_TOO_LARGE" in stack_trace


@pytest.mark.integration
def test_write_large_message_to_customised_topic(start_service, tmp_path):
    """Test writing a large message to a customised Kafka topic.

    Setup:
    - A dataset is created using a parameter to increase the maximum message size to 20MB.
    - A message of size ≈2MB is generated.

    Expectation: The message is written successfully without raising exceptions.
    """
    custom_yaml = """
pipeline:
  name: integration_test_write

  default_node_settings:
    num_cpus: 0.5

  nodes:
    sequence:
      class: tests.integration.test_kafka_topic_creation.CustomMessageWriter
      node_params:
        message_size: 2097152
      outputs:
        - message_dataset

  datasets:
    message_dataset:
      type: kafka_stream
      params:
        max.message.bytes: 20971520
    """
    custom_yaml_file = tmp_path / "custom_pipeline_config.yml"
    custom_yaml_file.write_text(custom_yaml)

    stack_trace = ""
    runner = Runner(pipeline_config_file=custom_yaml_file)

    try:
        runner.run()
    except ray.exceptions.RayActorError:
        # This is expected because we activated the poison pill
        stack_trace = traceback.format_exc()
        pass

    assert "MSG_SIZE_TOO_LARGE" not in stack_trace
