# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A series of cookiecutter post-codegen hooks to validate user input.

These code will run after files are generated

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""

import os

import yaml
from github import Auth, Github

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


def create_github_client() -> Github:
    """Creates a GitHub client.

    Returns:
        GitHub client.
    """
    if os.getenv("GITHUB_TOKEN"):
        return Github(auth=Auth.Token(os.environ["GITHUB_TOKEN"]))
    return Github()


def get_all_repo_contents(full_repo_rev: str) -> list:
    """Recursively gets all contents of a GitHub repo.

    Args:
        full_repo_rev: GitHub repo to clone,
            in the format of <<owner>>/<<repo>>#<<rev>>.

    Returns:
        List of all contents of the repo.
    """
    g = create_github_client()
    repo_rev = full_repo_rev.split("#")
    repo = g.get_repo(repo_rev[0])

    all_contents = []
    contents = repo.get_contents("", ref=repo_rev[1])
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(
                repo.get_contents(file_content.path, ref=repo_rev[1])
            )
        else:
            all_contents.append(file_content)
    g.close()
    return all_contents


def get_file_from_repo(full_repo_rev: str, file_path: str) -> str:
    """Gets a file from a GitHub repo.

    Args:
        full_repo_rev: GitHub repo to clone,
            in the format of <<owner>>/<<repo>>#<<rev>>.
        file_path: Path to file to get.

    Returns:
        Contents of file.
    """
    g = create_github_client()
    repo_rev = full_repo_rev.split("#")
    repo = g.get_repo(repo_rev[0])
    g.close()
    return repo.get_contents(file_path, ref=repo_rev[1]).decoded_content


def add_files_from_repo(full_repo_rev: str, project_slug: str):
    """Adds relevant files from the GitHub repo revision.

    Args:
        full_repo_rev: GitHub repo to clone,
            in the format of <<owner>>/<<repo>>#<<rev>>.
        project_slug: Project slug used for the generated project.
    """
    contents = get_all_repo_contents(full_repo_rev)

    # Parse aineko.yml
    project_config_raw = get_file_from_repo(full_repo_rev, "aineko.yml")
    project_config = yaml.safe_load(project_config_raw)
    project_config = ProjectConfig(**project_config)

    # Remove files that will be replaced
    os.remove(os.path.join(project_slug, "nodes.py"))
    os.remove(os.path.join("conf", "pipeline.yml"))

    # Add all files except aineko.yml
    for content in contents:
        if content.name == "aineko.yml":
            continue

        file_path = f"{content.path}"
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

        if os.path.dirname(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file:
            file.write(content.decoded_content)
