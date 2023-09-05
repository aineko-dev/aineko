"""Tests for the aineko.core.config_loader module."""

import copy
import os

import pytest

from aineko.core.config_loader import ConfigLoader

EXPECTED_TEST_RUN_1 = {
    "machine_config": {"type": "ec2", "mem": 16, "vcpu": 4},
    "aws_secrets": ["test/aineko_secret"],
    "catalog": {
        "integer_sequence": {
            "type": "kafka_stream",
            "params": {"retention.ms": 86400000},
        },
        "integer_doubles": {
            "type": "kafka_stream",
            "params": {"retention.ms": 86400000},
        },
        "env_var": {
            "type": "kafka_stream",
            "params": {"retention.ms": 86400000},
        },
    },
    "nodes": {
        "sequencer": {
            "class": "aineko.tests.conftest.TestSequencer",
            "outputs": ["integer_sequence", "env_var"],
            "params": {
                "start_int": "0",
                "num_messages": 25,
                "sleep_time": 1,
            },
        },
        "doubler": {
            "class": "aineko.tests.conftest.TestDoubler",
            "inputs": ["integer_sequence"],
            "outputs": ["integer_doubles"],
            "params": {"duration": 40},
        },
    },
}


def test_load_config(config_loader: type[ConfigLoader]) -> None:
    """Tests the loading of config.

    The config is loaded from test directory under the conf directory.

    Note: The test config is a subset of the actual config generated for the
    project. i.e. this does not test the config generated for the project
    base neither does it test config generated for local params since both
    change frequently.

    Args:
        config_loader (ConfigLoader): ConfigLoader fixture.
    """
    # Loading of all pipelines
    config = config_loader.load_config()

    # Remove local params
    for pipelines in config.values():
        for pipeline in pipelines.values():
            del pipeline["local_params"]

    expected_test_run_2 = copy.deepcopy(EXPECTED_TEST_RUN_1)
    expected_test_run_2["nodes"]["sequencer"]["params"]["start_int"] = "1"

    expected = {
        "test_project": {
            "test_run_1": EXPECTED_TEST_RUN_1,
            "test_run_2": expected_test_run_2,
        }
    }

    # Check that config is as expected
    for project_name, pipelines in expected.items():
        assert project_name in config
        assert config[project_name] == pipelines


def test_load_config_specified_pipelines(
    config_loader_single_pipeline: type[ConfigLoader],
) -> None:
    """Tests config loader where pipelines are specified.

    Args:
        config_loader_single_pipeline (ConfigLoader): ConfigLoader fixture.
    """
    # Loading single pipeline
    config = config_loader_single_pipeline.load_config()

    # Remove local params
    for pipelines in config.values():
        for pipeline in pipelines.values():
            del pipeline["local_params"]

    expected = {"test_project": {"test_run_1": EXPECTED_TEST_RUN_1}}
    assert config == expected


def test_load_config_test_pipelines(config_loader: type[ConfigLoader]) -> None:
    """Tests config loader for the test pipeline option. Pipelines should have
    the nodes patched according the config defined in test_pipelines.yml.

    Args:
        config_loader (ConfigLoader): ConfigLoader fixture.
    """

    config = config_loader.load_config(pipeline_tests=True)
    # pylint: disable=line-too-long
    expected = {
        "test_project": {
            "test_test_run_1": {
                "machine_config": {"type": "ec2", "mem": 16, "vcpu": 4},
                "catalog": {
                    "env_var": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
                    "integer_sequence": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
                    "integer_doubles": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
                },
                "nodes": {
                    "sequencer_patch": {
                        "class": "aineko.tests.test.pipeline_test.TestSequencerPatch",
                        "node_to_patch": "sequencer",
                        "outputs": ["integer_sequence"],
                    },
                    "doubler": {
                        "class": "aineko.tests.conftest.TestDoubler",
                        "inputs": ["integer_sequence"],
                        "outputs": ["integer_doubles"],
                        "params": {"duration": 40},
                    },
                    "doubler_checker": {
                        "class": "aineko.tests.test.pipeline_test.TestDoublerChecker",
                        "inputs": ["integer_doubles"],
                    },
                },
                "aws_secrets": ["test/aineko_secret"],
            },
        }
    }

    # Remove local_params from config
    for _, pipelines in config.items():
        for _, pipeline in pipelines.items():
            assert "local_params" in pipeline
            del pipeline["local_params"]

    assert config == expected
    # pylint: enable=line-too-long


def test_get_datasets_for_pipeline_nodes(config_loader: type[ConfigLoader]):
    """Tests the data extraction for pipeline struct nodes.

    Pipeline struct is a sub-struct of the config struct.
    e.g. config_struct = {
        'test_project': { #project struct
            'test_run_1': { # pipeline struct
                'nodes': {
                    'sequencer': {  # node struct
                        'class': 'aineko.tests.conftest.TestSequencer',
                        'outputs': ['integer_sequence', 'env_var'],
                        'params': {...}
                        },
                    'doubler': {  # node struct
                        'class': 'aineko.tests.conftest.TestDoubler',
                        'inputs': ['integer_sequence'],
                        'outputs': ['integer_doubles'],
                        'params': {...}
                        }
                    }}}
                    }

    Args:
        config_loader: test fixture for ConfigLoader
    """
    config = config_loader.load_config()
    datasets = config_loader.get_datasets_for_pipeline_nodes(
        config["test_project"]["test_run_1"]
    )
    assert sorted(list(datasets)) == sorted(
        ["env_var", "integer_doubles", "integer_sequence"]
    )


def test_get_datasets_for_pipeline_catalog(config_loader: type[ConfigLoader]):
    """Tests the data extraction for pipeline struct catalog.

    Pipeline struct is a sub-struct of the config struct.
    e.g. config_struct = {
        'test_project': { #project struct
            'test_run_1': { # pipeline struct
                'catalog': { #catalog struct
                    "integer_sequence": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
                    "integer_doubles": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
                    "env_var": {
                        "type": "kafka_stream",
                        "params": {"retention.ms": 86400000},
                    },
    },
                'nodes': {...}
                }
    }

    Args:
        config_loader: test fixture for ConfigLoader
    """
    config = config_loader.load_config()
    datasets = config_loader.get_datasets_for_pipeline_catalog(
        config["test_project"]["test_run_1"]
    )
    assert sorted(list(datasets)) == sorted(
        ["env_var", "integer_doubles", "integer_sequence"]
    )


def test_validate_config_datasets_pipeline_catalog_same_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the validation of datasets between pipeline and catalog.

    In this case, Catalog and pipeline have same datasets

    Pipeline struct is a sub-struct of the config struct.

    Args:
        config_loader: test fixture for ConfigLoader
    """
    base_config = config_loader.load_config()

    result1 = config_loader.validate_config_datasets_pipeline_catalog(
        base_config["test_project"]["test_run_1"]
    )
    assert result1 is True


def test_validate_config_datasets_pipeline_catalog_more_catalog_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the validation of datasets between pipeline and catalog.

    In this case, the catalog has more datasets than pipeline

    Pipeline struct is a sub-struct of the config struct.

    Args:
        config_loader: test fixture for ConfigLoader
    """
    base_config = config_loader.load_config()
    more_catalog_datasets = copy.deepcopy(
        base_config["test_project"]["test_run_1"]
    )
    more_catalog_datasets["catalog"]["new_dataset"] = (
        {
            "type": "kafka_stream",
            "params": {"retention.ms": 86400000},
        },
    )
    # for cases with more catalog datasets, the results are prescreened,
    # so the function should return True
    result2 = config_loader.validate_config_datasets_pipeline_catalog(
        more_catalog_datasets
    )
    assert result2 is True


def test_validate_config_datasets_pipeline_catalog_more_pipeline_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the validation of datasets between pipeline and catalog.

    In this case, the pipeline has more datasets than catalog

    We expect it to raise a ValueError.

    Pipeline struct is a sub-struct of the config struct.

    Args:
        config_loader: test fixture for ConfigLoader
    """
    base_config = config_loader.load_config()

    more_nodes_datasets = copy.deepcopy(
        base_config["test_project"]["test_run_1"]
    )
    more_nodes_datasets["nodes"]["sequencer"]["outputs"].append("new_dataset2")
    # expect ValueError if there are more datasets in pipeline nodes than catalog
    with pytest.raises(ValueError):
        config_loader.validate_config_datasets_pipeline_catalog(
            more_nodes_datasets
        )


def test_compare_data_code_and_catalog_same_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between python code and catalog.

    In this case, the catalog and python code have same datasets

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2"])
    code_datasets = set(["dataset1", "dataset2"])
    result = config_loader.compare_data_code_and_catalog(
        catalog_datasets=catalog_datasets, code_datasets=code_datasets
    )
    expected = {"catalog_only": set(), "code_only": set()}
    assert result == expected


def test_compare_data_code_and_catalog_more_catalog_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between python code and catalog.

    In this case, the catalog has more code than pipeline

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2"])
    code_datasets = set(["dataset1"])
    result = config_loader.compare_data_code_and_catalog(
        catalog_datasets=catalog_datasets, code_datasets=code_datasets
    )
    expected = {"catalog_only": set(["dataset2"]), "code_only": set()}
    assert result == expected


def test_compare_data_code_and_catalog_more_code_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between python code and catalog.

    In this case, the python code has more datasets than catalog

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1"])
    code_datasets = set(["dataset1", "dataset2"])
    result = config_loader.compare_data_code_and_catalog(
        catalog_datasets=catalog_datasets, code_datasets=code_datasets
    )
    expected = {"catalog_only": set(), "code_only": set(["dataset2"])}
    assert result == expected


def test_compare_data_pipeline_and_catalog_same_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between pipeline and catalog.

    In this case, the catalog and pipeline have same datasets

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2"])
    pipeline_datasets = set(["dataset1", "dataset2"])
    result = config_loader.compare_data_pipeline_and_catalog(
        catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
    )
    expected = {"catalog_only": set(), "pipeline_only": set()}
    assert result == expected


def test_compare_data_pipeline_and_catalog_more_catalog_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between pipeline and catalog.

    In this case, the catalog has more datasets than pipeline

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2", "new_dataset"])
    pipeline_datasets = set(["dataset1", "dataset2"])
    result = config_loader.compare_data_pipeline_and_catalog(
        catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
    )
    expected = {"catalog_only": {"new_dataset"}, "pipeline_only": set()}
    assert result == expected


def test_compare_data_pipeline_and_catalog_more_pipeline_datasets(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between pipeline and catalog.

    In this case, the pipeline has more datasets than catalog

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2"])
    pipeline_datasets = set(["dataset1", "dataset2", "new_dataset2"])
    result = config_loader.compare_data_pipeline_and_catalog(
        catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
    )
    expected = {"catalog_only": set(), "pipeline_only": {"new_dataset2"}}
    assert result == expected


def test_compare_data_pipeline_and_catalog_both_extra(
    config_loader: type[ConfigLoader],
):
    """Tests the comparison of datasets between pipeline and catalog.

    In this case, both the catalog and pipeline each have an extra dataset

    Args:
        config_loader: test fixture for ConfigLoader
    """
    catalog_datasets = set(["dataset1", "dataset2", "new_dataset"])
    pipeline_datasets = set(["dataset1", "dataset2", "new_dataset2"])
    result = config_loader.compare_data_pipeline_and_catalog(
        catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
    )
    expected = {
        "catalog_only": {"new_dataset"},
        "pipeline_only": {"new_dataset2"},
    }
    assert result == expected


def test_get_datasets_for_code(config_loader: type[ConfigLoader]):
    """Tests the extraction of dataset names from single code file.

    Results in a dictionary sorted by dataset type (producer vs. consumer)

    Args:
        config_loader: test fixture for ConfigLoader
    """
    result = config_loader.get_datasets_for_code("tests/test/pipeline_test.py")
    expected = {
        "producer_datasets": ["integer_sequence"],
        "consumer_datasets": ["integer_doubles"],
    }
    assert result == expected


def test_get_datasets_for_python_files(
    config_loader: type[ConfigLoader],
):
    """Tests the extraction of dataset names from multiple code files.

    Args:
        config_loader: test fixture for ConfigLoader
    """
    result = config_loader.get_datasets_for_python_files("tests/test")
    expected = set(["integer_sequence", "integer_doubles"])
    assert result == expected


def test__find_python_files(config_loader: type[ConfigLoader]):
    """Tests the finding of python files in a directory.

    Args:
        config_loader: test fixture for ConfigLoader
    """
    expected = ["pipeline_test.py"]
    result = config_loader._find_python_files("tests/test")
    assert [os.path.basename(x) for x in result] == expected
