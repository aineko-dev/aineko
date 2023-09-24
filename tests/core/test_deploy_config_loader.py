"""Tests for deploy_config_loader.py."""

import os

from aineko.core.deploy_config_loader import DeploymentConfigLoader


def test_load_deployment_config():
    """Test deployment config loader."""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "conf",
        "test_deploy.yml",
    )
    print(config_path)
    config_loader = DeploymentConfigLoader()
    user_config = config_loader.load_from_file(config_path)
    # Model should convert `8Gib` -> 8
    assert user_config.pipelines["example_pipeline"].machine_config.mem == 8
