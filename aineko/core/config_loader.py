"""Module to load config files."""
import ast
import glob
import os
from copy import deepcopy
from typing import Optional, Set, Union

from schema import Optional as optional
from schema import Schema, SchemaError

from aineko.config import AINEKO_CONFIG
from aineko.utils.io import load_yamls


class ConfigLoader:
    """Class to read yaml config files.

    Args:
            project: project name(s) to load config for
            conf_source: path of configuration files. Defaults
            to DEFAULT_CONF_SOURCE.

    Attributes:
            project (Union[str,list]): project name(s) to load config for
            conf_source (Union[str,None]): path of configuration files.
            config_schema (Schema): schema to validate config against

    Methods:
            load_config: load config for project(s) from yaml files
            validate_config: validate config against config_schema
    """

    def __init__(
        self,
        project: Optional[Union[str, list]] = None,
        conf_source: Optional[str] = None,
    ):
        """Initialize ConfigLoader."""
        self.conf_source = conf_source or AINEKO_CONFIG.get("CONF_SOURCE")

        # Enforce self.project is a list of project strings
        if isinstance(project, str):
            self.project = [project]
        elif not isinstance(project, list):
            raise ValueError(
                f"Project must be a string or list of strings/dicts. "
                f"Got {type(project)}"
            )
        else:
            self.project = project

        # Setup config schema
        self.config_schema = Schema(
            {
                # Pipeline config
                str: {
                    # Machine config
                    "machine_config": dict,
                    # Environment variables
                    optional("env_vars"): dict,
                    # Secrets
                    optional("aws_secrets"): list,
                    # Node config
                    "nodes": {
                        str: {
                            "class": str,
                            optional("params"): dict,
                            optional("inputs"): list,
                            optional("outputs"): list,
                            optional("node_to_patch"): str,
                        },
                    },
                    # Catalog config
                    "catalog": {
                        str: {
                            "type": str,
                            optional("params"): dict,
                        },
                    },
                    # Local params
                    "local_params": dict,
                },
            },
        )

    def compare_data_code_and_catalog(
        self, catalog_datasets: Set[str], code_datasets: Set[str]
    ) -> dict:
        """Compares datasets in code and catalog yaml files.

        Args:
            catalog_datasets: set of all catalog datasets
            code_datasets: set of all dataset names in code

        Returns:
            dict of datasets only in catalog and datasets only in code
        """
        catalog_only = catalog_datasets.difference(code_datasets)
        code_only = code_datasets.difference(catalog_datasets)
        return {"catalog_only": catalog_only, "code_only": code_only}

    def compare_data_pipeline_and_catalog(
        self, catalog_datasets: Set[str], pipeline_datasets: Set[str]
    ) -> dict:
        """Compares datasets in pipeline config and catalog yaml files.

        Args:
            catalog_datasets: set of all pipeline catalog datasets
            pipeline_datasets: set of all pipeline node datasets

        Returns:
            dict of datasets only in catalog and datasets only in pipeline
        """
        catalog_only = catalog_datasets.difference(pipeline_datasets)
        pipeline_only = pipeline_datasets.difference(catalog_datasets)
        return {"catalog_only": catalog_only, "pipeline_only": pipeline_only}

    def get_datasets_for_code(self, file_path: str) -> dict:
        """Parses python code to extract dataset names.

        Args:
            file_path: file path to python file

        Returns:
            dict of lists of producer and consumer dataset names
        """
        with open(file_path, "r", encoding="utf-8") as file:
            python_code = file.read()

        # Parse the code into an abstract syntax tree
        tree = ast.parse(python_code)

        # Initialize lists to store extracted strings
        producer_datasets = []
        consumer_datasets = []

        # Function to traverse the AST and extract dataset names
        def traverse_ast(node: ast.AST) -> None:
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Subscript)
                and isinstance(node.func.value.value, ast.Attribute)
                and isinstance(node.func.value.value.value, ast.Name)
                and node.func.value.value.value.id == "self"
                and isinstance(node.func.value.value.attr, str)
            ):
                if node.func.value.value.attr == "producers":
                    val = node.func.value.slice.value  # type: ignore
                    producer_datasets.append(val)
                elif node.func.value.value.attr == "consumers":
                    val = node.func.value.slice.value  # type: ignore
                    consumer_datasets.append(val)

            for child_node in ast.iter_child_nodes(node):
                traverse_ast(child_node)

        # Traverse the AST using the function
        traverse_ast(tree)
        producer_datasets = sorted(list(set(producer_datasets)))
        consumer_datasets = sorted(list(set(consumer_datasets)))
        return {
            "producer_datasets": producer_datasets,
            "consumer_datasets": consumer_datasets,
        }

    def get_datasets_for_python_files(self, project_dir: str) -> set:
        """Generates list of aineko datasets from python file in project_dir.

        Args:
            project_dir: directory containing python files

        Returns:
            all datasets in all reference python files
        """
        python_files = self._find_python_files(project_dir)
        all_producers = []
        all_consumers = []
        for python_file in python_files:
            dataset_dict = self.get_datasets_for_code(python_file)
            producers = dataset_dict["producer_datasets"]
            consumers = dataset_dict["consumer_datasets"]
            all_producers.extend(producers)
            all_consumers.extend(consumers)
        return set(all_producers).union(set(all_consumers))

    def load_config(self, pipeline_tests: bool = False) -> dict:
        """Load config for project(s) from yaml files.

        Steps for loading config:

        1. Setup config search params based on project

        2. Search for config files in conf_source

        3. Load all config files into a single config dict (catalog,
           pipelines, and local params)

        4a. Generate config for all pipelines in project

        4b. Generate config for test pipelines in project

        5. Filter config to only specified pipelines

        6. Validate project config against schema

        Example:
                {
                    "project_1": {
                        "pipeline_1": {...},
                        "pipeline_2": {...},
                    },
                    "project_2": {
                        "pipeline_1": {...},
                        "pipeline_2": {...},
                    },
                }

        Args:
            pipeline_tests: load only pipeline test configs

        Raises:
            ValueError: If project is not a string or list of strings

        Returns:
            Config for each project (dict keys are project names)
        """
        # Load config for each project
        config = {}
        for project in self.project:
            if isinstance(project, dict):
                project, pipelines = (
                    list(project.keys())[0],
                    list(project.values())[0],  # type: ignore
                )
            else:
                pipelines = None
            # 1. Setup config file search parameters based on project
            base_config_file_pattern = f"{self.conf_source}/base/*.yml"
            project_config_file_pattern = f"{self.conf_source}/{project}/*.yml"
            config_search_params = {
                "catalog": {
                    "dirs": [
                        base_config_file_pattern,
                        project_config_file_pattern,
                    ],
                    "only_names": ["catalog"],
                },
                "pipeline": {
                    "dirs": [
                        base_config_file_pattern,
                        project_config_file_pattern,
                    ],
                    "except_names": ["catalog", "test_"],
                },
                "pipeline_test_config": {
                    "dirs": [
                        base_config_file_pattern,
                        project_config_file_pattern,
                    ],
                    "only_names": ["test_"],
                },
                "local_params": {
                    "dirs": [f"{self.conf_source}/local/*.yml"],
                },
            }

            # 2. Fetch locations for all necessary config files for project
            config_files = {
                conf: self._find_config_files(**params)
                for conf, params in config_search_params.items()
            }

            # 3. Load all config files into an aggregated dictionary
            agg_config = {
                conf: load_yamls(files) for conf, files in config_files.items()
            }

            # 4a. Generate config for all project pipelines
            project_config = self._gen_project_config(agg_config)

            if pipeline_tests:
                # 4b. Generate config for test pipelines in project
                project_config = self._gen_test_pipeline_config(
                    project_config=project_config,
                    agg_config=agg_config,
                )

            # 5. Filter pipelines if specified
            filtered_project_config = self._filter_pipelines(
                project_config, pipelines
            )
            # 6. Validate config against schema
            try:
                self._validate_config_schema(
                    project_config=filtered_project_config
                )
            except SchemaError as e:
                raise SchemaError(
                    f"Schema validation failed for project `{project}`."
                    f"Config files loaded from {project_config_file_pattern} "
                    f"returned {filtered_project_config}."
                ) from e

            # Add project config to config
            config.update({project: filtered_project_config})

        return config

    def _find_config_files(
        self,
        dirs: list,
        only_names: Optional[list] = None,
        except_names: Optional[list] = None,
    ) -> list:
        """Get config files from a list of directories.

        Args:
            dirs: list of directories to search for config files
            only_names: only return files where any of these strings
                is contained in the file name
            except_names: exclude files where any of these strings
                is contained in the file name

        Returns:
            list of config files
        """
        # Search for all files in the relevant directories
        conf_files = []
        for cur_dir in dirs:
            conf_files.extend(glob.glob(cur_dir, recursive=True))

        # Restrict to only files with specific name, if specified
        if only_names:
            conf_files = [
                conf_file
                for conf_file in conf_files
                if any(
                    only_name in os.path.basename(conf_file)
                    for only_name in only_names
                )
            ]

        # Exclude files with specific name, if specified
        if except_names:
            conf_files = [
                conf_file
                for conf_file in conf_files
                if not any(
                    except_name in os.path.basename(conf_file)
                    for except_name in except_names
                )
            ]

        return conf_files

    def _find_python_files(
        self,
        project_dir: str,
        only_names: Optional[list] = None,
        except_names: Optional[list] = None,
    ) -> list:
        """Get python files from a directory.

        Args:
            project_dir: directory to search for python files
            only_names: only return files where any of these strings
                is contained in the file name
            except_names: exclude files where any of these strings
                is contained in the file name

        Returns:
            list of python files
        """
        dirs = [os.path.join(project_dir, "*.py")]
        return self._find_config_files(dirs, only_names, except_names)

    def _gen_project_config(self, agg_config: dict) -> dict:
        """Generate config for each pipeline in the project.

        If pipeline has runs, create a config for each run.

        Args:
            agg_config: Aggregated project config
            project: Project name

        Returns:
            project config
        """
        config = {}
        for pipeline_name, pipeline_conf in agg_config["pipeline"].items():
            # Reduce catalog to only include datasets used in the pipeline
            trimmed_catalog = self._trim_catalog(
                agg_config["catalog"], pipeline_conf["nodes"]
            )
            if "runs" in pipeline_conf:
                # Add pipeline config for each run to the project config
                for run_name, run_params in pipeline_conf["runs"].items():
                    config[run_name] = {
                        "machine_config": pipeline_conf["machine_config"],
                        "aws_secrets": pipeline_conf.get("aws_secrets", [""]),
                        "catalog": self._update_params(
                            trimmed_catalog, run_params
                        ),
                        "nodes": self._update_params(
                            pipeline_conf["nodes"], run_params
                        ),
                        "local_params": agg_config["local_params"],
                    }
            else:
                # Add pipeline config for the pipeline to the project config
                config[pipeline_name] = {
                    "machine_config": pipeline_conf["machine_config"],
                    "catalog": trimmed_catalog,
                    "aws_secrets": pipeline_conf.get("aws_secrets", [""]),
                    "nodes": pipeline_conf["nodes"],
                    "local_params": agg_config["local_params"],
                }

        return config

    def _gen_test_pipeline_config(
        self, project_config: dict, agg_config: dict
    ) -> dict:
        """Generate config for test pipelines detailed in test config.

        Args:
            project_config (dict): output of _gen_project_config
            agg_config (dict): config aggregated from all config files

        Returns:
            dict: pipeline config for test pipelines
        """
        test_config = {}

        for pipeline, pipeline_test_config in agg_config[
            "pipeline_test_config"
        ].items():
            pipeline_config = deepcopy(project_config[pipeline])
            # Patch nodes
            for node, node_config in pipeline_test_config.get(
                "patch_nodes", {}
            ).items():
                node_to_patch = node_config["node_to_patch"]
                if pipeline_config["nodes"].pop(node_to_patch) is None:
                    raise KeyError(
                        f"Node {node_to_patch} specified in {pipeline_config} "
                        "not found in pipeline {pipeline}"
                    )
                pipeline_config["nodes"][node] = node_config

            # Add checker nodes
            for node, node_config in pipeline_test_config.get(
                "checker_nodes", {}
            ).items():
                pipeline_config["nodes"][node] = node_config

            test_config[f"test_{pipeline}"] = pipeline_config

        return test_config

    @staticmethod
    def get_datasets_for_pipeline_nodes(pipeline_config: dict) -> set:
        """Get datasets for pipeline nodes.

        Args:
            pipeline_config: pipeline config derived from project config

        Returns:
            set of datasets
        """
        datasets = set()
        for node in pipeline_config["nodes"].values():
            if "inputs" in node:
                datasets.update(node["inputs"])
            if "outputs" in node:
                datasets.update(node["outputs"])
        return datasets

    @staticmethod
    def get_datasets_for_pipeline_catalog(pipeline_config: dict) -> set:
        """Get datasets for pipeline catalog.

        Args:
            pipeline_config: pipeline config derived from project config

        Returns:
            set of datasets
        """
        return set(pipeline_config["catalog"].keys())

    def _filter_pipelines(self, project_config: dict, pipelines: list) -> dict:
        """Filter pipelines in project config.

        Args:
            project_config: project config
            pipelines: list of pipelines to filter

        Returns:
            filtered project config
        """
        if pipelines:
            return {
                pipeline: pipeline_config
                for pipeline, pipeline_config in project_config.items()
                if pipeline in pipelines
            }
        else:
            return project_config

    def validate_config(self, project_config: dict) -> bool:
        """Validate config datasets and schema.

        Args:
            project_config: config to validate

        Raises:
            ValueError: if datasets in pipeline config are not in catalog
            SchemaError: if config is invalid

        Returns:
            True if config is valid
        """
        # Validate config against schema
        self._validate_config_schema(project_config)

        # Validate that all datasets in pipeline config are in catalog
        for pipeline_config in project_config.values():
            self.validate_config_datasets_pipeline_catalog(pipeline_config)

        return True

    def _validate_config_schema(self, project_config: dict) -> bool:
        """Validate config.

        Note:
        e.g. schema -
        {
            "project_name": {
                "pipeline_name": {
                    "machine_config": dict,
                    "aws_secrets": list,
                    "catalog": dict,
                    "nodes": dict,
                    "local_params": dict,
                }
            }
        }

        For more information on schema validation,
        see: https://github.com/keleshev/schema

        Args:
            project_config: config to validate

        Raises:
            SchemaError: if config is invalid

        Returns:
            True if config is valid
        """
        self.config_schema.validate(project_config)
        return True

    @staticmethod
    def _trim_catalog(catalog: dict, nodes: dict) -> dict:
        """Trim catalog to only include datasets used in pipeline.

        Args:
            catalog: catalog to trim
            nodes: nodes in pipeline

        Returns:
            trimmed catalog
        """
        datasets = set()
        for node in nodes.values():
            if "inputs" in node:
                datasets.update(node["inputs"])
            if "outputs" in node:
                datasets.update(node["outputs"])
        return {k: v for k, v in catalog.items() if k in datasets}

    def validate_config_datasets_pipeline_catalog(
        self, pipeline_config: dict
    ) -> bool:
        """Validate that all datasets in pipeline config are in catalog.

        Args:
            pipeline_config: pipeline config derived from project config

        Raises:
            ValueError: if datasets in pipeline config are not in catalog

        Returns:
            True if all datasets in pipeline config are in catalog
        """
        set_differences = self.compare_data_pipeline_and_catalog(
            self.get_datasets_for_pipeline_catalog(pipeline_config),
            self.get_datasets_for_pipeline_nodes(pipeline_config),
        )
        pipeline_only = set_differences["pipeline_only"]
        if pipeline_only:
            raise ValueError(
                "The following datasets in the pipeline config "
                "yaml are not defined in the catalog yaml: "
                f"{pipeline_only}"
            )
        return True

    def _update_params(
        self, value: Union[dict, list, str, int], params: dict
    ) -> Union[dict, list, str, int]:
        """Update value with params.

        Recursively calls the method if value is a list or dictionary until it
        reaches a string or int. If string then formats the str with variable
        mapping in params dict.

        Args:
            value: value to update
            params: params to update value with

        Returns:
            object with updated values (dict, list, str, or int)
        """
        if isinstance(value, dict):
            new_dict_val = {}
            for key, val in value.items():
                new_dict_val[key] = self._update_params(val, params)
            return new_dict_val
        if isinstance(value, list):
            new_list_val: list = []
            for val in value:
                new_list_val.append(self._update_params(val, params))
            return new_list_val
        if isinstance(value, str):
            for key, val in params.items():
                value = value.replace(f"${key}", val)
            return value
        if isinstance(value, (int, float)):
            return value
        raise ValueError(
            f"Invalid value type {type(value)}. "
            "Expected dict, list, str, or int."
        )
