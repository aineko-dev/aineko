# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A series of cookiecutter post-codegen hooks to validate user input.

These code will run after files are generated

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""

import os

import yaml
from github import Github, Repository

from aineko import __version__
from aineko.models.project_config_schema import ProjectConfig


def remove_deploy_file():
    """Remove deploy file if it exists."""
    try:
        deploy_file_path = os.path.join(os.getcwd(), "deploy.yml")
        if os.path.isfile(deploy_file_path):
            os.remove(deploy_file_path)
    except FileNotFoundError:
        pass


def get_all_repo_contents(repo: Repository, ref: str):
    """Recursively gets all contents of a GitHub repo.

    Args:
        repo: github Repository object.
    """
    all_contents = []
    contents = repo.get_contents("", ref=ref)
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
    else:
        all_contents.append(file_content)
    return all_contents


def add_files_from_repo(full_repo_rev: str):
    """Adds relevant files from the GitHub repo revision to the
    generated aineko project.

    Args:
        full_repo_rev: GitHub repo to clone,
            in the format of <<owner>>/<<repo>>#<<rev>>.
    """
    g = Github()
    repo, ref = full_repo_rev.split("#")
    repo = g.get_repo(repo)

    # Parse aineko.yml
    project_config_raw = repo.get_contents("aineko.yml", ref=ref)
    project_config = yaml.safe_load(project_config_raw.decoded_content)
    project_config = ProjectConfig(**project_config)

    contents = get_all_repo_contents(repo, ref)

    # Add all files except aineko.yml
    for content in contents:
        if content.name == "aineko.yml":
            continue
        file_path = os.path.join(os.getcwd(), content.path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(content.decoded_content)
