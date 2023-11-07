# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0

import pytest
from click.testing import CliRunner

from aineko import __version__
from aineko.__main__ import aineko
from aineko.cli.create_pipeline import create


def test_aineko_version():
    """Test that aineko CLI can return version info."""
    runner = CliRunner()
    result = runner.invoke(aineko, ["--version"])
    assert result.exit_code == 0
    assert result.output == f"aineko, version {__version__}\n"


def test_aineko_create(tmp_path):
    """Test that pipeline template can be created."""
    runner = CliRunner()
    result = runner.invoke(
        create, ["-d", "--output-dir", str(tmp_path), "--no-input"]
    )
    assert result.exit_code == 0
    assert (tmp_path / "my_awesome_pipeline").is_dir()
    assert (
        tmp_path / "my_awesome_pipeline" / "conf" / "pipeline.yml"
    ).is_file()
    assert (tmp_path / "my_awesome_pipeline" / "deploy.yml").is_file()
    assert (
        tmp_path / "my_awesome_pipeline" / "my_awesome_pipeline" / "nodes.py"
    ).is_file()


@pytest.mark.integration
def test_aineko_service():
    """Test service CLI functions, requires docker."""
    runner = CliRunner()
    result = runner.invoke(aineko, ["service", "start"])
    assert result.exit_code == 0
    result = runner.invoke(aineko, ["service", "restart"])
    assert result.exit_code == 0
    result = runner.invoke(aineko, ["service", "stop"])
    assert result.exit_code == 0


@pytest.mark.integration
def test_aineko_run(tmp_path):
    """Test run CLI functions, requires docker."""
    runner = CliRunner()

    result = runner.invoke(aineko, ["service", "restart"])
    assert result.exit_code == 0

    result = runner.invoke(
        create, ["-d", "--output-dir", str(tmp_path), "--no-input"]
    )
    assert result.exit_code == 0

    assert (tmp_path / "my_awesome_pipeline/conf/pipeline.yml").is_file()
    result = runner.invoke(
        aineko,
        [
            "run",
            str(tmp_path / "my_awesome_pipeline/conf/pipeline.yml"),
            "--pipeline-name",
            "test-pipeline",
        ],
    )
    assert result.output == ""
