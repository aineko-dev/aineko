"""Tests for the aineko.core.config_loader module."""

import copy
import os

import pytest

from aineko.core.config_loader import ConfigLoader

EXPECTED_TEST_PIPELINE = {
    "pipeline": {
        "name": "test_pipeline",
        "nodes": {
            "sequencer": {
                "class": "aineko.tests.conftest.TestSequencer",
                "outputs": ["integer_sequence", "env_var"],
                "class_params": {
                    "start_int": 0,
                    "num_messages": 25,
                    "sleep_time": 1,
                },
            },
            "doubler": {
                "class": "aineko.tests.conftest.TestDoubler",
                "inputs": ["integer_sequence"],
                "outputs": ["integer_doubles"],
                "class_params": {"duration": 40},
            },
        },
        "datasets": {
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
    }
}

EXPECTED_TEST_PIPELINE_RUNS = copy.deepcopy(EXPECTED_TEST_PIPELINE)
EXPECTED_TEST_PIPELINE_RUNS["pipeline"]["name"] = "test_run_1"
EXPECTED_TEST_PIPELINE_RUNS["pipeline"]["nodes"]["sequencer"]["class_params"][
    "start_int"
] = "0"


def test_load_config(
    config_loader: ConfigLoader,
    config_loader_runs: ConfigLoader,
) -> None:
    """Tests the loading of config.

    The config is loaded from test directory under the conf directory.
    """
    config = config_loader.load_config()
    assert config == EXPECTED_TEST_PIPELINE

    # Test config loader for pipeline config with runs
    config_runs = config_loader_runs.load_config()
    assert config_runs == EXPECTED_TEST_PIPELINE_RUNS


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


# def test_get_datasets_for_pipeline_catalog(config_loader: type[ConfigLoader]):
#     """Tests the data extraction for pipeline struct catalog.

#     Pipeline struct is a sub-struct of the config struct.
#     e.g. config_struct = {
#         'test_project': { #project struct
#             'test_run_1': { # pipeline struct
#                 'catalog': { #catalog struct
#                     "integer_sequence": {
#                         "type": "kafka_stream",
#                         "params": {"retention.ms": 86400000},
#                     },
#                     "integer_doubles": {
#                         "type": "kafka_stream",
#                         "params": {"retention.ms": 86400000},
#                     },
#                     "env_var": {
#                         "type": "kafka_stream",
#                         "params": {"retention.ms": 86400000},
#                     },
#     },
#                 'nodes': {...}
#                 }
#     }

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     config = config_loader.load_config()
#     datasets = config_loader.get_datasets_for_pipeline_catalog(
#         config["test_project"]["test_run_1"]
#     )
#     assert sorted(list(datasets)) == sorted(
#         ["env_var", "integer_doubles", "integer_sequence"]
#     )


# def test_validate_config_datasets_pipeline_catalog_same_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the validation of datasets between pipeline and catalog.

#     In this case, Catalog and pipeline have same datasets

#     Pipeline struct is a sub-struct of the config struct.

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     base_config = config_loader.load_config()

#     result1 = config_loader.validate_config_datasets_pipeline_catalog(
#         base_config["test_project"]["test_run_1"]
#     )
#     assert result1 is True


# def test_validate_config_datasets_pipeline_catalog_more_catalog_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the validation of datasets between pipeline and catalog.

#     In this case, the catalog has more datasets than pipeline

#     Pipeline struct is a sub-struct of the config struct.

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     base_config = config_loader.load_config()
#     more_catalog_datasets = copy.deepcopy(
#         base_config["test_project"]["test_run_1"]
#     )
#     more_catalog_datasets["catalog"]["new_dataset"] = (
#         {
#             "type": "kafka_stream",
#             "params": {"retention.ms": 86400000},
#         },
#     )
#     # for cases with more catalog datasets, the results are prescreened,
#     # so the function should return True
#     result2 = config_loader.validate_config_datasets_pipeline_catalog(
#         more_catalog_datasets
#     )
#     assert result2 is True


# def test_validate_config_datasets_pipeline_catalog_more_pipeline_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the validation of datasets between pipeline and catalog.

#     In this case, the pipeline has more datasets than catalog

#     We expect it to raise a ValueError.

#     Pipeline struct is a sub-struct of the config struct.

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     base_config = config_loader.load_config()

#     more_nodes_datasets = copy.deepcopy(
#         base_config["test_project"]["test_run_1"]
#     )
#     more_nodes_datasets["nodes"]["sequencer"]["outputs"].append("new_dataset2")
#     # expect ValueError if there are more datasets in pipeline nodes than catalog
#     with pytest.raises(ValueError):
#         config_loader.validate_config_datasets_pipeline_catalog(
#             more_nodes_datasets
#         )


# def test_compare_data_code_and_catalog_same_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between python code and catalog.

#     In this case, the catalog and python code have same datasets

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2"])
#     code_datasets = set(["dataset1", "dataset2"])
#     result = config_loader.compare_data_code_and_catalog(
#         catalog_datasets=catalog_datasets, code_datasets=code_datasets
#     )
#     expected = {"catalog_only": set(), "code_only": set()}
#     assert result == expected


# def test_compare_data_code_and_catalog_more_catalog_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between python code and catalog.

#     In this case, the catalog has more code than pipeline

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2"])
#     code_datasets = set(["dataset1"])
#     result = config_loader.compare_data_code_and_catalog(
#         catalog_datasets=catalog_datasets, code_datasets=code_datasets
#     )
#     expected = {"catalog_only": set(["dataset2"]), "code_only": set()}
#     assert result == expected


# def test_compare_data_code_and_catalog_more_code_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between python code and catalog.

#     In this case, the python code has more datasets than catalog

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1"])
#     code_datasets = set(["dataset1", "dataset2"])
#     result = config_loader.compare_data_code_and_catalog(
#         catalog_datasets=catalog_datasets, code_datasets=code_datasets
#     )
#     expected = {"catalog_only": set(), "code_only": set(["dataset2"])}
#     assert result == expected


# def test_compare_data_pipeline_and_catalog_same_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between pipeline and catalog.

#     In this case, the catalog and pipeline have same datasets

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2"])
#     pipeline_datasets = set(["dataset1", "dataset2"])
#     result = config_loader.compare_data_pipeline_and_catalog(
#         catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
#     )
#     expected = {"catalog_only": set(), "pipeline_only": set()}
#     assert result == expected


# def test_compare_data_pipeline_and_catalog_more_catalog_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between pipeline and catalog.

#     In this case, the catalog has more datasets than pipeline

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2", "new_dataset"])
#     pipeline_datasets = set(["dataset1", "dataset2"])
#     result = config_loader.compare_data_pipeline_and_catalog(
#         catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
#     )
#     expected = {"catalog_only": {"new_dataset"}, "pipeline_only": set()}
#     assert result == expected


# def test_compare_data_pipeline_and_catalog_more_pipeline_datasets(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between pipeline and catalog.

#     In this case, the pipeline has more datasets than catalog

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2"])
#     pipeline_datasets = set(["dataset1", "dataset2", "new_dataset2"])
#     result = config_loader.compare_data_pipeline_and_catalog(
#         catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
#     )
#     expected = {"catalog_only": set(), "pipeline_only": {"new_dataset2"}}
#     assert result == expected


# def test_compare_data_pipeline_and_catalog_both_extra(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the comparison of datasets between pipeline and catalog.

#     In this case, both the catalog and pipeline each have an extra dataset

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     catalog_datasets = set(["dataset1", "dataset2", "new_dataset"])
#     pipeline_datasets = set(["dataset1", "dataset2", "new_dataset2"])
#     result = config_loader.compare_data_pipeline_and_catalog(
#         catalog_datasets=catalog_datasets, pipeline_datasets=pipeline_datasets
#     )
#     expected = {
#         "catalog_only": {"new_dataset"},
#         "pipeline_only": {"new_dataset2"},
#     }
#     assert result == expected


# def test_get_datasets_for_code(config_loader: type[ConfigLoader]):
#     """Tests the extraction of dataset names from single code file.

#     Results in a dictionary sorted by dataset type (producer vs. consumer)

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     result = config_loader.get_datasets_for_code(
#         "tests/artifacts/sample_nodes/nodes.py"
#     )
#     expected = {
#         "producer_datasets": ["integer_sequence"],
#         "consumer_datasets": ["integer_doubles"],
#     }
#     assert result == expected


# def test_get_datasets_for_python_files(
#     config_loader: type[ConfigLoader],
# ):
#     """Tests the extraction of dataset names from multiple code files.

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     result = config_loader.get_datasets_for_python_files(
#         "tests/artifacts/sample_nodes"
#     )
#     expected = set(["integer_sequence", "integer_doubles"])
#     assert result == expected


# def test_find_python_files(config_loader: type[ConfigLoader]):
#     """Tests the finding of python files in a directory.

#     Args:
#         config_loader: test fixture for ConfigLoader
#     """
#     expected = ["nodes.py"]
#     result = config_loader._find_python_files("tests/artifacts/sample_nodes")
#     assert set([os.path.basename(x) for x in result]) == set(expected)
