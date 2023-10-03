# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Loads deployment config for an aineko project.

Users define their deployment configuration in a user-friendly format
that is then converted into a full deployment config. The user-friendly
format is more compact, and follows the schema that can be found in
the DeploymentConfig model.

The full deployment config is a comprehensive mapping between
every pipeline and its deployment configuration. It is the source
of truth in which infrastructure should be deployed from.
"""
from collections import defaultdict
from typing import Optional

from pydantic.utils import deep_update

from aineko.models.deploy_config_schema import (
    DeploymentConfig,
    FullDeploymentConfig,
)
from aineko.utils.io import load_yaml


def generate_deploy_config_from_file(
    user_config_file: str, config_type: str = "full"
) -> dict:
    """Generates full or user deployment config from deployment config file.

    Args:
        user_config_file: path to the deployment config file
        type: `full` or `user`. If `full`, returns the full deployment config

    Returns:
        Full or user deployment configuration.
    """
    user_config = load_yaml(user_config_file)
    config = generate_deploy_config(user_config, config_type=config_type)
    return config


def generate_deploy_config(
    user_config: dict, config_type: str = "full"
) -> dict:
    """Generates full or user deployment config from the input user config dict.

    Args:
        user_config: deployment configuration in the user-friendly
            format. See DeploymentConfig for expected schema.

    Returns:
        Full or user deployment configuration.
    """
    if config_type not in ["full", "user"]:
        raise ValueError(
            "Specified output config type must be either `full` or `user`"
        )

    user_deploy_config = DeploymentConfig(**user_config)
    if config_type == "user":
        return user_deploy_config.dict()

    else:
        full_config = _generate_full_config(user_deploy_config)
        return full_config.dict()


def _generate_full_config(
    user_config: Optional[DeploymentConfig] = None,
) -> FullDeploymentConfig:
    """Generates a full deployment config from the user config.

    For each pipeline specified in each environment, we start with the
    default config, then override with all pipeline-specific config,
    then override with all environment-specific config.

    Args:
        user_config: deployment configuration in the user-friendly format.
        See DeploymentConfig for expected schema.

    Returns:
        Full deployment configuration.
    """
    user_config = user_config or user_config
    if not user_config:
        raise ValueError("User config has not been loaded nor defined.")

    full_config: dict = {
        "version": user_config.version,
        "environments": defaultdict(lambda: {"pipelines": {}}),
    }

    for env_name, env_pipelines in user_config.environments.items():
        for (
            pipeline_name,
            pipeline_values,
        ) in env_pipelines.pipelines.items():
            defaults = (
                user_config.defaults.dict() if user_config.defaults else {}
            )
            pipeline_specific_config = {
                k: v
                for k, v in user_config.pipelines[pipeline_name].dict().items()
                if v
            }

            # Env specific config may not be defined
            env_specific_config = {
                k: v for k, v in pipeline_values.dict().items() if v
            }

            # Env-specific overwrites pipeline-specific overwrites defaults
            full_config["environments"][env_name]["pipelines"][
                pipeline_name
            ] = deep_update(
                defaults,
                pipeline_specific_config,
                env_specific_config,
            )

    return FullDeploymentConfig(**full_config)
