"""Tests for deploy_config_loader.py."""

from aineko.core.deploy_config_loader import generate_deploy_config_from_file
from aineko.models.deploy_config_schema import FullDeploymentConfig
from aineko.utils.io import load_yaml


def test_load_deployment_config(deploy_config_path, full_deploy_config_path):
    """Test deployment config loader."""
    user_config = generate_deploy_config_from_file(
        deploy_config_path, config_type="user"
    )

    assert user_config

    full_config = generate_deploy_config_from_file(deploy_config_path)
    expected_full_config = load_yaml(full_deploy_config_path)
    expected_full_config = FullDeploymentConfig(**expected_full_config).dict()
    assert full_config == expected_full_config
