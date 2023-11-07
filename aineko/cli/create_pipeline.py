# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Utils to create a aineko pipeline from existing templates."""

import os

import click
from cookiecutter.main import cookiecutter  # type: ignore


@click.command()
@click.option(
    "--deployment-config",
    "-d",
    is_flag=True,
    help="Include deploy.yml that facilitates deployment of pipelines.",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    help="Directory to create pipeline in. Defaults to current directory.",
)
@click.option(
    "--no-input",
    "-n",
    is_flag=True,
    help="Do not prompt for parameters and use defaults.",
)
def create(deployment_config: bool, output_dir: str, no_input: bool) -> None:
    """Creates boilerplate code and config required for an Aineko pipeline.

    Args:
        deployment_config: If True, include a deploy file when generating, else
        do not include.
        output_dir: Directory to create pipeline in. Defaults to current.
        no_input: If True, do not prompt for parameters and use defaults.
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # assumes templates is a folder that is one-level up
    templates_directory = f"{os.path.dirname(script_directory)}/templates"
    # Only one type of pipeline, hence this argument is no-arg
    cookiecutter(
        f"{templates_directory}/first_aineko_pipeline",
        extra_context={
            "_deployment_config": deployment_config,
        },
        output_dir=output_dir,
        no_input=no_input,
    )
