# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A series of cookiecutter post-codegen hooks to validate user input.

These code will run after files are generated

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""
import os
import sys

# Color codes for logging
ERROR = "\x1b[1;31m[ERROR]: "
TERMINATOR = "\x1b[0m"


project_slug = "{{cookiecutter.project_slug}}"
with_deploy_str = "{{ cookiecutter._deployment_config }}"

# Cast string to boolean
if with_deploy_str.lower() == "true":
    with_deploy = True
elif with_deploy_str.lower() == "false":
    with_deploy = False
else:
    print(
        ERROR + f"Invalid value for cookiecutter._deployment_config:"
        f" {with_deploy_str}" + TERMINATOR
    )
    sys.exit(1)


def validate_deploy_file_path(file_path: str) -> None:
    """Validates that path to deploy.yaml points to a file.

    Args:
        file_path: The path to deploy.yml file

    Raises:
        FileNotFoundError: If the 'deploy.yml' file does not exist.
    """
    # Check if the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")


def _get_deploy_file_path() -> str:
    # The hook runs in the newly created project
    file_path = os.path.join(os.getcwd(), "deploy.yml")
    return file_path


try:
    deploy_file_path = _get_deploy_file_path()
    validate_deploy_file_path(deploy_file_path)
    if not with_deploy:
        os.remove(deploy_file_path)


except FileNotFoundError as ex:
    print(ERROR + str(ex) + TERMINATOR)
    sys.exit(1)
