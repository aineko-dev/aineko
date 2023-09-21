"""Module to load config files."""
import ast
from typing import Any, List, Optional, Union, overload

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
        pipeline_config_file (str): path to pipeline configuration file
        pipeline (Union[str,list]): pipeline name to load config for
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
                    optional("default_node_settings"): dict,
                    # Node config
                    "nodes": {
                        str: {
                            "class": str,
                            optional("node_params"): dict,
                            optional("node_settings"): dict,
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
            except KeyError as exc:
                raise KeyError(
                    f"Specified pipeline `{self.pipeline}` not in pipelines "
                    f"found in config: {list(configs)}."
                ) from exc
            config["pipeline"].pop("runs")

        try:
            self._validate_config_schema(pipeline_config=config)
        except SchemaError as e:
            raise SchemaError(
                f"Schema validation failed for pipeline "
                f"`{config['pipeline']['name']}`."
                f"Config files loaded from {self.pipeline_config_file} "
                f"returned {config}."
            ) from e

        # If pipeline name specified, check against config pipeline name
        if self.pipeline and config["pipeline"]["name"] != self.pipeline:
            raise KeyError(
                f"Specified pipeline `{self.pipeline}` not found in config "
                f"file: `{self.pipeline_config_file}`"
            )

        return config

    def _validate_config_schema(self, pipeline_config: dict) -> bool:
        """Validate config.

        Note:
        e.g. schema -
        {
            "pipeline": {
                "name": str,
                "nodes": dict,
                "datasets": dict,
            }
        }

        For more information on schema validation,
        see: https://github.com/keleshev/schema

        Args:
            pipeline_config: config to validate

        Raises:
            SchemaError: if config is invalid

        Returns:
            True if config is valid
        """
        self.config_schema.validate(pipeline_config)
        return True

    @overload
    def _update_params(self, value: dict, params: dict) -> dict:
        ...

    @overload
    def _update_params(self, value: list, params: dict) -> list:
        ...

    @overload
    def _update_params(self, value: str, params: dict) -> str:
        ...

    @overload
    def _update_params(self, value: int, params: dict) -> int:
        ...

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


class ConfigLoaderValidator:
    """Validates datasets in config loader struct.

    Attributes:
        config_loader (config_loader):

        config (dict): config struct generated by config_loader.load_config()

        validation_struct (dict): data structure containing dataset
        information for nodes_config, datasets, and node_code.

    Args:
        config_loader: ConfigLoader class to validate
    """

    def __init__(self, config_loader: ConfigLoader):
        """Creates ConfigLoaderValidator instance."""
        self.config_loader: Optional[ConfigLoader] = config_loader
        self.config = self.config_loader.load_config()
        self.validation_struct: Any = None

    def build_validation_struct(self) -> None:
        """Create data structure to be used in dataset validation.

            The dictionary is divided into three sections:
                1. datasets: a set of datasets defined in the pipeline config
                file.

                2. nodes_config: a dictionary containing inputs/outputs datasets
                per node class defined in the pipeline config file.

                3. nodes_code: a dictionary containing inputs/outputs datasets
                (consumers/producers) obtained from parsing the python code from
                the class defined in the pipeline config file.

            Schema:

            validation_struct = {
            'datasets': {
                'integer_doubles',
                'integer_sequence',
                'env_var'
            },
            'nodes_config': {
                'nodes': {
                    'tests.conftest.TestSequencer': {
                        'inputs': set([]),
                        'outputs': set(['integer_sequence', 'env_var'])
                    },
                    'tests.conftest.TestDoubler': {
                        'inputs': set(['integer_sequence']),
                        'outputs': set(['integer_doubles'])
                    }
                },
                'all_datasets': {
                    'integer_doubles',
                    'integer_sequence',
                    'env_var'
                }
            },
            'nodes_code': {
                'nodes': {
                    'tests.conftest.TestSequencer': {
                        'inputs': set([]),
                        'outputs': set(['integer_sequence'])
                    },
                    'tests.conftest.TestDoubler': {
                        'inputs': set(['integer_sequence']),
                        'outputs': set(['integer_doubles'])
                    }
                },
                'all_datasets': {
                    'integer_doubles',
                    'integer_sequence'
                }
            }
        }
        """
        validation_struct = {
            "datasets": self._get_config_datasets(self.config),
            "nodes_config": self._get_nodes_config(self.config),
            "nodes_code": self._get_nodes_code(self.config),
        }
        self.validation_struct = validation_struct

    def _get_config_datasets(self, config: dict) -> set:
        """Parse and return a set of unique datasets from pipeline.yml file.

        Extracts unique dataset names from the `datasets` section of the
        pipeline config yaml file.

        Args:
            config: config struct generated from config_loader.load_config()

        Returns:
            set of unique dataset names
        """
        return set(config["pipeline"].get("datasets", {}).keys())

    def _get_nodes_config(self, config: dict) -> dict:
        """Builds datasets struct for nodes defined in pipeline.yml file.

        Args:
            config: config struct generated from config_loader.load_config()

        Returns:
            nodes config struct of the form:

            {
            'nodes': {
                'tests.conftest.TestSequencer': {
                    'inputs': set([]),
                    'outputs': set(['integer_sequence', 'env_var'])
                },
                'tests.conftest.TestDoubler': {
                    'inputs': set(['integer_sequence']),
                    'outputs': set(['integer_doubles'])
                }
            },
            'all_datasets': {
                'integer_doubles',
                'integer_sequence',
                'env_var'
            }
        """
        nodes = config["pipeline"].get("nodes", {})
        nodes_config: dict[str, Any] = {
            "nodes": {
                v["class"]: {
                    "inputs": set(v.get("inputs", [])),
                    "outputs": set(v.get("outputs", [])),
                }
                for _, v in nodes.items()
            },
            "all_datasets": set([]),
        }
        all_datasets: List[str] = []
        for _, vals in nodes_config["nodes"].items():
            all_datasets.extend(vals["inputs"])
            all_datasets.extend(vals["outputs"])
        nodes_config["all_datasets"] = set(all_datasets)
        return nodes_config

    def _get_node_code(self, class_path: str) -> dict:
        """Extracts node code datasets struct based on class path.

        Uses the `class` attribute defined in the pipeline config
        nodes section to locate the code file and class name for
        extracting datasets information.

        Uses ast to traverse the python code class and locate
        occurrences of consumers[consumer_name].consume() and
        producers[producer_name].produce().

        Appends `consume_name` to the list of inputs for the node,
        and appends `producer_name` to the list of outputs for the node.

        Args:
            class_path: `class` attribute of a node in the pipeline.yml
            config file.

        Returns:
            single node code struct, of the form:
            {class_path: {"inputs": set([dataset_input1, dataset_input2,...]),
                          "outputs": set([dataset_output1, dataset_output2,...])
                          }}
        """
        class_name = class_path.split(".")[-1]
        file_path = "/".join(class_path.split(".")[:-1]) + ".py"
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            tree = ast.parse(content)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break
        if class_node is None:
            raise ValueError(
                f"Class {class_name} not found in file {file_path}"
            )

        inputs = []
        outputs = []

        def traverse_ast(node: ast.AST) -> None:
            """Collects producers and consumers from code."""
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
                    outputs.append(val)
                elif node.func.value.value.attr == "consumers":
                    val = node.func.value.slice.value  # type: ignore
                    inputs.append(val)

            for child_node in ast.iter_child_nodes(node):
                traverse_ast(child_node)

        print(type(class_node))
        traverse_ast(class_node)  # arg-type: ignore
        node_code = {
            class_path: {"inputs": set(inputs), "outputs": set(outputs)}
        }
        return node_code

    def _get_nodes_code(self, config: dict) -> dict:
        """Collects node code dataset structs across all nodes.

        Calls the _get_node_code() method across all instances
        of the nodes defined in the pipeline.yml config file.

        Collects all nodes into a nodes_code struct to be used in
        the validation_struct.

        Args:
            config: config struct generated from config_loader.load_config()

        Returns:
            nodes code struct of the form:

            {
                'nodes': {
                    'tests.conftest.TestSequencer': {
                        'inputs': set(),
                        'outputs': set(['integer_sequence'])
                    },
                    'tests.conftest.TestDoubler': {
                        'inputs': set(['integer_sequence']),
                        'outputs': {['integer_doubles']}
                    }
                },
                'all_datasets': {
                    'integer_doubles',
                    'integer_sequence'
                }
            }

        """
        nodes = config["pipeline"].get("nodes", {})
        nodes_code: Any = {"nodes": {}}
        all_datasets: List[str] = []
        for _, node_data in nodes.items():
            class_path = node_data["class"]
            node_code = self._get_node_code(class_path)
            for class_name, inputs_outputs in node_code.items():
                nodes_code["nodes"][class_name] = inputs_outputs
                all_datasets.extend(inputs_outputs["inputs"])
                all_datasets.extend(inputs_outputs["outputs"])
        nodes_code["all_datasets"] = set(all_datasets)
        return nodes_code

    def validate_nodes_config_datasets(self) -> bool:
        """Compares pipeline yml datasets with pipeline nodes datasets.

        Checks that the set of all inputs/outputs datasets defined by the
        nodes in the pipeline.yml config file is a subset of the set of all
        datasets defined in the datasets section of the pipeline.yml config
        file.

        Returns:
            True if node datasets are subset of pipeline datasets else False.
        """
        if self.validation_struct is None:
            self.build_validation_struct()
        return self.validation_struct["nodes_config"][  # type:ignore
            "all_datasets"
        ].issubset(  # type:ignore
            self.validation_struct["datasets"]  # type: ignore
        )

    def validate_nodes_config_nodes_code(self) -> bool:
        """Compares the code datasets with pipeline config node datasets.

        Takes each node defined in the pipeline config file, and compares its
        inputs/outputs datasets against the inputs/outputs datasets defined in
        the corresponding python code class.
        """
        if self.validation_struct is None:
            self.build_validation_struct()
        top_node_config = self.validation_struct["nodes_config"]  # type: ignore
        nodes_config = top_node_config["nodes"]  # type: ignore
        top_nodes_code = self.validation_struct["nodes_code"]  # type: ignore
        nodes_code = top_nodes_code["nodes"]  # type: ignore
        for node, node_config_data in nodes_config.items():
            nodes_code_data = nodes_code[node]
            if nodes_code_data != node_config_data:
                print(
                    f"FOR NODE CLASS {node}:\n"
                    f"nodes code data: \n {nodes_code_data} \n "
                    f"does not match node config data: \n{node_config_data}"
                )
                return False
        return True
