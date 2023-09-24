"""Loads deployment config for an aineko project."""

from aineko.models.deploy_config import DeploymentConfig
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
        self.user_config = None
        self.full_config = None

    def load(self, user_config: dict) -> dict:
        """Generates a full deployment config from the user config.

        Args:
            user_config (dict): deployment configuration in the user-friendly
                format. See DeploymentConfig for expected schema.
        """
        deployment_config = DeploymentConfig(**user_config)
        return deployment_config

    def load_from_file(self, user_config_file: str) -> dict:
        """Generates full deployment config from a given deployment config file.

        Args:
            user_config_file (str): path to the deployment config file.
        """
        user_config = load_yaml(user_config_file)
        full_config = self.load(user_config)
        return full_config
