# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A series of cookiecutter post-codegen hooks to validate user input.

These code will run after files are generated

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""

from aineko.templates.first_aineko_pipeline.hooks.utils import (
    add_files_from_repo,
    remove_deploy_file,
)
from aineko.utils.misc import truthy

with_deploy = "{{ cookiecutter._deployment_config }}"
repo = "{{ cookiecutter._repo }}"
project_slug = "{{ cookiecutter.project_slug }}"

if not truthy(with_deploy):
    remove_deploy_file()

if repo != "None":
    add_files_from_repo(repo, project_slug)
