"""Tests for deploy_config_loader.py."""

import os

import pytest

from aineko.core.deploy_config_loader import DeploymentConfigLoader
from aineko.models.deploy_config import FullDeploymentConfig
from aineko.utils.io import load_yaml


@pytest.fixture(scope="module")
def deploy_config_path():
    """Deployment config yml path."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "conf",
        "test_deploy.yml",
    )


@pytest.fixture(scope="module")
def full_deploy_config_path():
    """Deployment config yml path."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "conf",
        "test_deploy_full.yml",
    )


def test_load_deployment_config(deploy_config_path, full_deploy_config_path):
    """Test deployment config loader."""
    config_loader = DeploymentConfigLoader()
    full_config = config_loader.load_from_file(deploy_config_path)
    user_config = config_loader.get_user_config()

    # Model should convert `8Gib` -> 8
    assert (
        user_config["pipelines"]["example_pipeline"]["machine_config"]["mem"]
        == 8
    )

    expected_full_config = load_yaml(full_deploy_config_path)
    expected_full_config = FullDeploymentConfig(**expected_full_config).dict()
    assert full_config == expected_full_config
