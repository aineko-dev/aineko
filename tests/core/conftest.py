# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test fixtures for tests."""

import os

import pytest


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
