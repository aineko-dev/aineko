# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
import pytest
from pydantic import ValidationError

from aineko.models.config_schema import Config


def test_node_log_to_dataset(node_log_to_dataset, subtests):
    """Test node log_to_dataset."""
    with subtests.test("Test if the yml config is valid"):
        assert Config(**node_log_to_dataset)

    validated_config = Config(**node_log_to_dataset)

    with subtests.test(
        "Test if the nodes have the expected logging parmameters"
    ):
        assert (
            validated_config.pipeline.nodes["with_logging"].log_to_dataset
            is True
        )
        assert (
            validated_config.pipeline.nodes["without_logging"].log_to_dataset
            is None
        )
        assert (
            validated_config.pipeline.nodes["with_logging"].logging_namespace
            == "okenia"
        )


def test_pipeline_log_to_dataset(pipeline_log_to_dataset, subtests):
    """Test pipeline log_to_dataset."""
    with subtests.test("Test if the yml config is valid"):
        assert Config(**pipeline_log_to_dataset)

    validated_config = Config(**pipeline_log_to_dataset)

    with subtests.test(
        "Test if the nodes have the expected logging parmameters"
    ):
        assert (
            validated_config.pipeline.nodes["nothing_specified"].log_to_dataset
            is True
        )
        assert (
            validated_config.pipeline.nodes["no_logging"].log_to_dataset
            is False
        )
        assert (
            validated_config.pipeline.nodes[
                "nothing_specified"
            ].logging_namespace
            == "okenia"
        )
        assert (
            validated_config.pipeline.nodes["no_logging"].logging_namespace
            == "okenia"
        )


def test_pipeline_dont_log_to_dataset(pipeline_dont_log_to_dataset, subtests):
    """Test pipeline log_to_dataset."""
    with subtests.test("Test if the yml config is valid"):
        assert Config(**pipeline_dont_log_to_dataset)

    validated_config = Config(**pipeline_dont_log_to_dataset)

    with subtests.test(
        "Test if the nodes have the expected logging parmameters"
    ):
        assert (
            validated_config.pipeline.nodes["nothing_specified"].log_to_dataset
            is False
        )
        assert (
            validated_config.pipeline.nodes["logging_enabled"].log_to_dataset
            is True
        )
        assert (
            validated_config.pipeline.nodes[
                "nothing_specified"
            ].logging_namespace
            is None
        )
        assert (
            validated_config.pipeline.nodes["logging_enabled"].logging_namespace
            == "okenia"
        )


def test_invalid_pipeline_log_to_dataset(invalid_pipeline_log_to_dataset):
    """Test invalid pipeline log_to_dataset."""
    with pytest.raises(ValidationError):
        Config(**invalid_pipeline_log_to_dataset)


def test_invalid_node_log_to_dataset(invalid_node_log_to_dataset):
    """Test invalid pipeline log_to_dataset."""
    with pytest.raises(ValidationError):
        Config(**invalid_node_log_to_dataset)
