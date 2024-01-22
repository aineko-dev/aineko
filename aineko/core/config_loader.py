# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to load config files."""
import logging
from typing import overload

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
        config_schema (Config): Pydantic model to validate a pipeline config

    Methods:
        load_config: loads and validates the pipeline config from a yaml file
    """

    def __init__(
        self,
        pipeline_config_file: str,
    ):
        """Initialize ConfigLoader."""
        self.pipeline_config_file = pipeline_config_file or AINEKO_CONFIG.get(
            "DEFAULT_PIPELINE_CONFIG"
        )

        # Setup config schema
        self.config_schema = Config

    def load_config(self) -> dict:
        """Load and validate the pipeline config.

        Raises:
            ValidationError: If the config does not match the schema

        Returns:
            The pipeline config as a dictionary
        """
        config = load_yaml(self.pipeline_config_file)

        try:
            Config(**config)
        except ValidationError as e:
            logger.error(
                "Schema validation failed for pipeline `%s` loaded from %s. "
                "See detailed error below.",
                config["pipeline"]["name"],
                self.pipeline_config_file,
            )
            raise e

        return config
