# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for cookiecutter hooks."""

from aineko.templates.first_aineko_pipeline.hooks.utils import (
    get_all_repo_contents,
)


def test_get_all_repo_contents():
    """Test that all contents of a repo are retrieved."""
    contents = get_all_repo_contents("aineko-dev/aineko-dream#main")
    assert len(contents) > 1
