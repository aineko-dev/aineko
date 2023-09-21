"""Tests for the aineko.core.config_loader module."""

import copy

import pytest

from aineko.core.config_loader import ConfigLoader, ConfigLoaderValidator

EXPECTED_TEST_PIPELINE = {
    "pipeline": {
        "name": "test_pipeline",
        "nodes": {
            "sequencer": {
                "class": "tests.conftest.TestSequencer",
                "outputs": ["integer_sequence"],
                "node_params": {
                    "start_int": 0,
                    "num_messages": 25,
                    "sleep_time": 1,
                },
            },
            "doubler": {
                "class": "tests.conftest.TestDoubler",
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
            "integer_doubles": {"type": "kafka_stream"},
            "env_var": {"type": "kafka_stream"},
        },
    },
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


def test_validate_nodes_config_datasets(test_pipeline_config_file: str) -> None:
    """Tests ConfigLoaderValidator nodes config and datasets.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file are a subset
    of the set of datasets defined in the datasests section of the
    pipeline config yml file.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    assert config_loader_validator.validate_nodes_config_nodes_code()


def test_validate_nodes_config_node_code(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and node code.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file match with
    the datasets defined in the python code.

    Comparison is performed on a node-by-node basis.

    inputs of node1 are compared with the consumers in the code
    defined in the class of node1.

    outputs of node1 are compared with the producers in the code
    defined in the class of node1.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    assert config_loader_validator.validate_nodes_config_nodes_code()


def test_validate_nodes_config_datasets_extra_datasets(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and datasets.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file are a subset
    of the set of datasets defined in the datasests section of the
    pipeline config yml file.

    In this variant, we add an extra dataset to the 'datasets'
    section of the config file. The validation should be True,
    because the node config should still be a subset of a larger set.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    config_loader_validator.config = config_loader_validator.config_loader.load_config()
    # add an extra dataset to the 'datasets' section of config file.
    print(config_loader_validator.config)
    config_loader_validator.config["pipeline"]["datasets"]["extra_var"] = {
        "type": "kafka_stream"
    }
    assert config_loader_validator.validate_nodes_config_datasets()


def test_validate_nodes_config_datasets_extra_nodes_inputs(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and datasets.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file are a subset
    of the set of datasets defined in the datasests section of the
    pipeline config yml file.

    In this variant, we add an extra dataset to the inputs of a node
    of the config file. The validation should be False,
    because the node config should will no longer be a subset of the `datasets`.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    config_loader_validator.config = config_loader_validator.config_loader.load_config()
    # add an extra dataset to the 'datasets' section of config file.
    config_loader_validator.config["pipeline"]["nodes"]["doubler"][
        "inputs"
    ].append("extra_var")
    assert config_loader_validator.validate_nodes_config_datasets() is False

def test_validate_nodes_config_datasets_extra_nodes_outputs(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and datasets.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file are a subset
    of the set of datasets defined in the datasests section of the
    pipeline config yml file.

    In this variant, we add an extra dataset to the outputs of a node
    of the config file. The validation should be False,
    because the node config should will no longer be a subset of the `datasets`.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    config_loader_validator.config = config_loader_validator.config_loader.load_config()
    # add an extra dataset to the 'datasets' section of config file.
    config_loader_validator.config["pipeline"]["nodes"]["doubler"][
        "outputs"
    ].append("extra_var")
    assert config_loader_validator.validate_nodes_config_datasets() is False

def test_validate_nodes_config_node_code_extra_node_inputs(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and node code.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file match with
    the datasets defined in the python code.

    Comparison is performed on a node-by-node basis.

    inputs of node1 are compared with the consumers in the code
    defined in the class of node1.

    outputs of node1 are compared with the producers in the code
    defined in the class of node1.

    In this variant, we add an extra dataset to the node config inputs.

    Therefore, we expect the validation to be False.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    config_loader_validator.config = config_loader_validator.config_loader.load_config()
    config_loader_validator.config["pipeline"]["nodes"]["doubler"]["inputs"].append("extra_var")
    assert config_loader_validator.validate_nodes_config_nodes_code() is False

def test_validate_nodes_config_node_code_extra_node_outputs(
    test_pipeline_config_file: str,
) -> None:
    """Tests ConfigLoaderValidator nodes config and node code.

    Validates that the datasets defined in all inputs/outputs
    across all nodes in the pipeline config yml file match with
    the datasets defined in the python code.

    Comparison is performed on a node-by-node basis.

    inputs of node1 are compared with the consumers in the code
    defined in the class of node1.

    outputs of node1 are compared with the producers in the code
    defined in the class of node1.

    In this variant, we add an extra dataset to the node config outputs.

    Therefore, we expect the validation to be False.

    Args:
        test_pipeline_config_file: path to test pipeline config yml file

    Returns:
        None
    """
    config_loader = ConfigLoader(test_pipeline_config_file)
    config_loader_validator = ConfigLoaderValidator(config_loader)
    config_loader_validator.config = config_loader_validator.config_loader.load_config()
    config_loader_validator.config["pipeline"]["nodes"]["doubler"]["outputs"].append("extra_var")
    assert config_loader_validator.validate_nodes_config_nodes_code() is False