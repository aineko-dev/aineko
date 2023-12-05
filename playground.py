# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
import yaml
from github import Github

from aineko.models.project_config_schema import ProjectConfig

g = Github()

branch = "ba5c5c76-47c6-45a9-b3b5-8ce00ce500ce"

repo = g.get_repo("Convex-Labs/dream-catcher")

file = repo.get_contents("aineko.yml", ref=branch)

decoded = file.decoded_content

project_config = yaml.safe_load(decoded)

project_config = ProjectConfig(**project_config)
