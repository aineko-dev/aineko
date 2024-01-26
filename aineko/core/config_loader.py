# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to load config files."""
import logging
import os
import re
from typing import Dict, List, Optional, Union, overload

from pydantic import ValidationError

from aineko.config import AINEKO_CONFIG
from aineko.models.config_schema import Config
from aineko.utils.io import load_yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Class to read yaml config files.

    Args:
        pipeline_config_file: path of pipeline config file. Defaults
            to `DEFAULT_PIPELINE_CONFIG`.

    Attributes:
        pipeline_config_file (str): path to the pipeline configuration file

    Methods:
        load_config: loads and validates the pipeline config from a yaml file
        inject_env_vars: injects environment variables into node params
    """

    def __init__(
        self,
        pipeline_config_file: str,
    ):
        """Initialize ConfigLoader."""
        self.pipeline_config_file = pipeline_config_file or AINEKO_CONFIG.get(
            "DEFAULT_PIPELINE_CONFIG"
        )

    def load_config(self) -> Config:
        """Load and validate the pipeline config.

        Raises:
            ValidationError: If the config does not match the schema

        Returns:
            The validated pipeline config as a Pydantic Config object
        """
        raw_config = load_yaml(self.pipeline_config_file)

        try:
            config = Config(**raw_config)
        except ValidationError as e:
            logger.error(
                "Schema validation failed for pipeline `%s` loaded from %s. "
                "See detailed error below.",
                raw_config["pipeline"]["name"],
                self.pipeline_config_file,
            )
            raise e

        # Inject environment variables into node params
        for node in config.pipeline.nodes.values():
            if node.node_params is not None:
                node.node_params = self.inject_env_vars(node.node_params)

        return config

    @overload
    def inject_env_vars(self, node_params: dict) -> dict:
        ...

    @overload
    def inject_env_vars(self, node_params: list) -> list:
        ...

    @overload
    def inject_env_vars(self, node_params: str) -> str:
        ...

    @overload
    def inject_env_vars(self, node_params: int) -> int:
        ...

    @overload
    def inject_env_vars(self, node_params: float) -> float:
        ...

    @overload
    def inject_env_vars(self, node_params: Optional[None]) -> None:
        ...

    def inject_env_vars(
        self,
        node_params: Optional[Union[Dict, List, str, int, float, bool]] = None,
    ) -> Optional[Union[Dict, List, str, int, float, bool]]:
        """Inject environment variables into node params.

        This function is used to recursively inject environment variables
        into strings passed through node params via the pipeline config.
        We only recursively parse strings, dicts, and lists, as these are
        the only types that can contain environment variables (i.e.
        excluding ints, floats, and Nones).

        Environment variables are identified in strings by the pattern
        {$ENV_VAR} where ENV_VAR is the name of the environment variable
        to inject. For example, given the following environment variables:

        ```
        $ export SECRET1=secret1
        $ export SECRET2=secret2
        ```

        The following node params dict:

            ```
            {
                "key1": "A string with a {$SECRET1} and a {$SECRET2}.",
                "key2": {
                    "key3": "A string with a {$SECRET1} and a {$SECRET2}.",
                    "key4": [
                        "A string with a {$SECRET1} and a {$SECRET2}.",
                        "A string with a {$SECRET1} and a {$SECRET2}."
                    ]
                }
            }
            ```

        Will be transformed to:

                ```
                {
                    "key1": "A string with a secret1 and a secret2.",
                    "key2": {
                        "key3": "A string with a secret1 and a secret2.",
                        "key4": [
                            "A string with a secret1 and a secret2.",
                            "A string with a secret1 and a secret2."
                        ]
                    }
                }
                ```
        """
        if isinstance(node_params, dict):
            for k, v in list(node_params.items()):
                node_params[k] = self.inject_env_vars(v)
        elif isinstance(node_params, list):
            for i, v in enumerate(node_params):
                node_params[i] = self.inject_env_vars(v)
        elif isinstance(node_params, str):
            env_var_pattern = r"\{\$.*?\}"
            env_var_match = re.search(env_var_pattern, node_params, re.DOTALL)
            if env_var_match:
                env_var_env_str = env_var_match.group()
                env_var_value = os.getenv(
                    env_var_env_str[2:][:-1], default=None
                )
                if env_var_value is None:
                    raise ValueError(
                        "Failed to inject environment variable. "
                        f"{env_var_env_str[2:][:-1]} was not found."
                    )
                node_params = node_params.replace(
                    env_var_env_str, env_var_value
                )
                return self.inject_env_vars(node_params)

        return node_params
