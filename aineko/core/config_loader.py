"""Module to load config files."""
import ast
import glob
import os
from typing import Optional, Set, Union

from schema import Optional as optional
from schema import Schema, SchemaError

from aineko.config import AINEKO_CONFIG
from aineko.utils.io import load_yamls


class ConfigLoader:
    """Class to read yaml config files.

    Args:
            pipeline: pipeline name to load config for
            pipeline_config_file: path of pipeline config file. Defaults
            to DEFAULT_CONF_SOURCE.

    Attributes:
            pipeline (Union[str,list]): pipeline name to load config for
            pipeline_config_file (Union[str,None]): path to pipeline configuration file.
            config_schema (Schema): schema to validate config against

    Methods:
            load_config: load config for project(s) from yaml files
            validate_config: validate config against config_schema
    """

    def __init__(
        self,
        pipeline_config_file: str,
        pipeline: Optional[str] = None,
    ):
        """Initialize ConfigLoader."""
        self.pipeline_config_file = pipeline_config_file or AINEKO_CONFIG.get(
            "DEFAULT_PIPELINE_CONFIG"
        )
        self.pipeline = pipeline

        # Setup config schema
        self.config_schema = Schema(
            {
                # Runs
                optional("runs"): dict,
                # Pipeline config
                "pipeline": {
                    "name": str,
                    optional("default_node_params"): dict,
                    # Node config
                    "nodes": {
                        str: {
                            "class": str,
                            optional("class_params"): dict,
                            optional("node_params"): dict,
                            optional("inputs"): list,
                            optional("outputs"): list,
                        },
                    },
                    # Datasets config
                    "datasets": {
                        str: {
                            "type": str,
                            optional("params"): dict,
                        },
                    },
                },
            },
        )

    def load_config(self) -> dict:
        """Load config for project(s) from yaml files.

        Load the config from the specified pipeline config. If runs detected,
        create all runs and filter out the selected one. Will only return config
        for a single pipeline.

        Example:
                {
                    "pipeline": {
                        "name": ...,
                        "nodes": {...},
                        "datasets": {...}
                    },
                }

        Raises:
            ValueError: If project is not a string or list of strings

        Returns:
            Config for each project (dict keys are project names)
        """
        config = load_yamls(self.pipeline_config_file)

        if "runs" in config["pipeline"]:
            configs = {}
            for run_name, run_params in config["pipeline"]["runs"].items():
                configs[run_name] = self._update_params(config, run_params)
                configs[run_name]["pipeline"]["name"] = run_name
            try:
                config = configs[self.pipeline]
            except KeyError:
                raise KeyError(
                    f"Specified pipeline `{self.pipeline}` not in pipelines "
                    f"found in config: {list(configs)}."
                )
            config["pipeline"].pop("runs")

        try:
            self._validate_config_schema(project_config=config)
        except SchemaError as e:
            raise SchemaError(
                f"Schema validation failed for pipeline `{config['pipeline']['name']}`."
                f"Config files loaded from {self.pipeline_config_file} "
                f"returned {config}."
            ) from e
        return config

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
