"""Tests for aineko.cli.provision module."""

import os

from aineko.cli.provision import get_active_projects


def test_get_active_projects(conf_directory):
    """Test get_active_projects function."""
    test_conf_source = os.path.join(conf_directory, "main.yml")
    active_projects = get_active_projects(
        env="develop", config_file=test_conf_source
    )
    expected = [{"test_1": ["test_pipeline_1"]}, "test_2"]
    assert active_projects == expected

    test_conf_source = os.path.join(conf_directory, "blank.yml")
    active_projects = get_active_projects(
        env="develop", config_file=test_conf_source
    )
    assert active_projects == []
