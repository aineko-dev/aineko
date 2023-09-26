"""Loads deployment config for an aineko project."""

from collections import defaultdict
from typing import Optional, Union

from pydantic.utils import deep_update

from aineko.models.deploy_config import DeploymentConfig, FullDeploymentConfig
from aineko.utils.io import load_yaml


class DeploymentConfigLoader:
    """Loads deployment config for an aineko project.

    Users define their deployment configuration in a user-friendly format
    that is then converted into a full deployment config. The user-friendly
    format is more compact, and follows the schema that can be found in
    the DeploymentConfig model.

    The full deployment config is a comprehensive mapping between
    every pipeline and its deployment configuration. It is the source
    of truth in which infrastructure should be deployed from.

    Attributes:
        user_config (dict): deployment config in the user-friendly format

    """

    def __init__(self) -> None:
        """Initialize DeploymentConfigLoader."""
        self.user_config: Optional[DeploymentConfig] = None
        self.full_config: Optional[FullDeploymentConfig] = None

    def load(self, user_config: dict) -> dict:
        """Generates a full deployment config from the user config.

        Args:
            user_config (dict): deployment configuration in the user-friendly
                format. See DeploymentConfig for expected schema.

        Returns:
            dict: full deployment configuration
        """
        self.user_config = DeploymentConfig(**user_config)
        self.full_config = self.generate_full_config(self.user_config)
        return self.full_config.dict()

    def load_from_file(self, user_config_file: str) -> dict:
        """Generates full deployment config from a given deployment config file.

        Args:
            user_config_file (str): path to the deployment config file.

        Returns:
            dict: full deployment configuration
        """
        user_config = load_yaml(user_config_file)
        full_config = self.load(user_config)
        return full_config

    def generate_full_config(
        self, user_config: Optional[DeploymentConfig] = None
    ) -> FullDeploymentConfig:
        """Generates a full deployment config from the user config.

        For each pipeline specified in each environment, we start with the
        default config, then override with all pipeline-specific config,
        then override with all environment-specific config.

        Args:
            user_config (DeploymentConfig): deployment configuration in the
            user-friendly format. See DeploymentConfig for expected schema.

        Returns:
            FullDeploymentConfig: full deployment configuration
        """
        user_config = user_config or self.user_config
        if not user_config:
            raise ValueError("User config has not been loaded nor defined.")
        full_config: dict = {
            "project": user_config.project,
            "version": user_config.version,
            "environments": defaultdict(lambda: {"pipelines": []}),
        }
        for env, env_pipelines in user_config.environments.items():
            for pipeline in env_pipelines.pipelines:
                if isinstance(pipeline, str):
                    pipeline_name = pipeline
                else:
                    # Get first key in dict
                    pipeline_name = next(iter(pipeline))

                defaults = (
                    user_config.defaults.dict() if user_config.defaults else {}
                )
                pipeline_specific_config = {
                    k: v
                    for k, v in user_config.pipelines[pipeline_name]
                    .dict()
                    .items()
                    if v
                }

                # Env specific config may not be defined
                if isinstance(pipeline, dict):
                    env_specific_config = {
                        k: v
                        for k, v in pipeline[pipeline_name].dict().items()
                        if v
                    }
                else:
                    env_specific_config = {}

                # Env-specific overwrites pipeline-specific overwrites defaults
                full_config["environments"][env]["pipelines"].append(
                    {
                        pipeline_name: deep_update(
                            defaults,
                            pipeline_specific_config,
                            env_specific_config,
                        )
                    }
                )
        return FullDeploymentConfig(**full_config)

    def get_user_config(
        self, json: bool = True
    ) -> Union[dict, DeploymentConfig]:
        """Returns user config.

        Args:
            json (bool): whether to return as json or not
        """
        if self.user_config is None:
            raise ValueError("User config has not been loaded yet.")
        if json:
            return self.user_config.dict()
        else:
            return self.user_config

    def get_full_config(
        self, json: bool = True
    ) -> Union[dict, FullDeploymentConfig]:
        """Returns full config.

        Args:
            json (bool): whether to return as json or not
        """
        if self.full_config is None:
            raise ValueError("User config has not been loaded yet.")
        if json:
            return self.full_config.dict()
        else:
            return self.full_config
