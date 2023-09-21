"""Tests for the aineko.core.config_loader module."""

import copy

import pytest

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

EXPECTED_TEST_PIPELINE_RUNS = copy.deepcopy(EXPECTED_TEST_PIPELINE)
EXPECTED_TEST_PIPELINE_RUNS["pipeline"]["name"] = "test_run_1"
EXPECTED_TEST_PIPELINE_RUNS["pipeline"]["nodes"]["sequencer"]["node_params"][
    "start_int"
] = "0"


def test_load_config(
    test_pipeline_config_file: str,
    test_pipeline_config_file_runs: str,
) -> None:
    """Tests the loading of config.

    The config is loaded from test directory under the conf directory.
    """
    # Test pipeline config containing single pipeline
    config = ConfigLoader(test_pipeline_config_file).load_config()
    assert config == EXPECTED_TEST_PIPELINE

    # Test pipeline config containing single pipeline while specifying correct pipeline name
    config = ConfigLoader(
        test_pipeline_config_file, pipeline="test_pipeline"
    ).load_config()
    assert config == EXPECTED_TEST_PIPELINE

    # Test pipeline config containing single pipeline while specifying wrong pipeline name
    with pytest.raises(KeyError):
        config = ConfigLoader(
            test_pipeline_config_file, pipeline="wrong_name"
        ).load_config()

    # Test config loader for pipeline config with runs
    config_runs = ConfigLoader(
        test_pipeline_config_file_runs, pipeline="test_run_1"
    ).load_config()
    assert config_runs == EXPECTED_TEST_PIPELINE_RUNS

    # Ensures error if attempt to load pipeline config with run without specifying run
    with pytest.raises(KeyError):
        config_runs = ConfigLoader(test_pipeline_config_file_runs).load_config()
