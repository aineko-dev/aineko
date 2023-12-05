# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A series of cookiecutter post-codegen hooks to validate user input.

These code will run after files are generated

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""
from aineko.utils.misc import truthy

from .utils import add_files_from_repo, remove_deploy_file

with_deploy = "{{ cookiecutter._deployment_config }}"
repo = "{{ cookiecutter._repo }}"

if not truthy(with_deploy):
    remove_deploy_file()

if truthy(repo):
    add_files_from_repo()
