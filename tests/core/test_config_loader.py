# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the aineko.core.config_loader module."""

import pytest
from pydantic import ValidationError

from aineko.core.config_loader import ConfigLoader

EXPECTED_TEST_PIPELINE = {
    "pipeline": {
        "name": "test_pipeline",
        "default_node_settings": {
            "num_cpus": 0.5,
        },
        "nodes": {
            "sequencer": {
                "class": "aineko.tests.conftest.TestSequencer",
                "outputs": ["integer_sequence", "env_var"],
                "node_params": {
                    "start_int": 0,
                    "num_messages": 25,
                    "sleep_time": 1,
                },
            },
            "doubler": {
                "class": "aineko.tests.conftest.TestDoubler",
                "inputs": ["integer_sequence"],
                "outputs": ["integer_doubles"],
                "node_params": {"duration": 40},
            },
            "dummy": {"class": "aineko.tests.conftest.DummyNode"},
        },
        "datasets": {
            "integer_sequence": {
                "type": "kafka_stream",
                "params": {"retention.ms": 86400000},
            },
            "integer_doubles": {
                "type": "kafka_stream",
            },
            "env_var": {
                "type": "kafka_stream",
            },
        },
    }
}


def test_load_config(
    test_pipeline_config_file: str,
) -> None:
    """Tests the loading of config.

    The config is loaded from test directory under the conf directory.
    """
    # Test pipeline config containing single pipeline
    config = ConfigLoader(test_pipeline_config_file).load_config()
    assert config == EXPECTED_TEST_PIPELINE


def test_load_invalid_config(test_invalid_pipeline_config_file: str, caplog):
    """Tests the loading of an invalid config.

    The class name is missing from the doubler node definition.
    We expect a ValidationError to be raised.
    """
    with pytest.raises(ValidationError) as err:
        ConfigLoader(test_invalid_pipeline_config_file).load_config()
    assert err.value.errors() == [
        {
            "loc": ("pipeline", "nodes", "doubler", "class"),
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]
    # Capture the log output
    captured = caplog.records[0].message
    # Check that the correct informational message is logged
    assert (
        captured
        == f"Schema validation failed for pipeline `test_invalid_pipeline` "
        f"loaded from {test_invalid_pipeline_config_file}. See detailed error "
        "below."
    )
