# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Utils to create a aineko pipeline from existing templates."""

import os

import click
from cookiecutter.main import cookiecutter  # type: ignore


@click.command()
@click.option(
    "-d",
    "--deployment-config",
    is_flag=True,
    help="Include deploy.yml that facilitates deployment of pipelines.",
)
@click.option(
    "-o",
    "--output-dir",
    default=".",
    help="Directory to create pipeline in. Defaults to current directory.",
)
@click.option(
    "-n",
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and use defaults.",
)
@click.option(
    "-r",
    "--repo",
    help=(
        "GitHub repo to create pipeline from. Link should contain branch or "
        "rev to reference. "
        "(Ex aineko-dev/dream-catcher#my-branch) "
        "Refer to CLI docs for more info on repo structure."
    ),
)
def create(
    deployment_config: bool, output_dir: str, no_input: bool, repo: str
) -> None:
    """Creates boilerplate code and config required for an Aineko pipeline.\f

    If repo is set, attempts to clone and use the files from the repo.
    The following files are required:

        - aineko.yml: Contains required data to create an aineko pipeline.
            Requires keys:
            - aineko_version: Version of aineko to use.
            - project_name: Name of the aineko project.
            - project_slug (optional): Slug of project. Can only contain
                alphanumeric characters and underscores. Will be derived from
                project_name if not provided.
            - project_description (optional): Description of the pipeline.
            - pipeline_slug (optional): Name of pipeline.
        - <<project_name>>/nodes.py or <<project_name>>/nodes/*.py: Either a
            file containing all node code or a directory containing multiple
            node code files.
        - conf/*.yml: Directory containing config files for pipelines.

    The following files are optional, and will overwrite the default files:
        - README.md (optional): README file for the repo.
        - pyproject.toml: Project configuration, including poetry requirements
        - deploy.yml: Project deployment configuration.
        - <<project_name>>/tests/*.py: Test directory

    Args:
        deployment_config: If True, include a deploy file when generating, else
        do not include.
        output_dir: Directory to create pipeline in. Defaults to current.
        no_input: If True, do not prompt for parameters and use defaults.
        repo: GitHub repo to create pipeline from. Link should contain branch
            or rev to reference.
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # assumes templates is a folder that is one-level up
    templates_directory = f"{os.path.dirname(script_directory)}/templates"
    # Only one type of pipeline, hence this argument is no-arg
    cookiecutter(
        f"{templates_directory}/first_aineko_pipeline",
        extra_context={
            "_deployment_config": deployment_config,
            "_repo": repo,
        },
        output_dir=output_dir,
        no_input=no_input,
    )
