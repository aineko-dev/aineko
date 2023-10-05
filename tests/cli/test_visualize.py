# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
import py
import pytest

from aineko.cli.visualize import (
    build_mermaid_from_yaml,
    render_graph_in_browser,
    render_mermaid_graph,
)


def test_build_mermaid_from_yaml(
    subtests, pipeline_config_path: str, rendered_pipeline: dict
):
    """Test mermaid graph builder."""
    with subtests.test("Test build_mermaid_from_yaml, LR"):
        graph = build_mermaid_from_yaml(pipeline_config_path, direction="LR")
        assert (
            graph
            == f"{rendered_pipeline['header']['LR']}\n{rendered_pipeline['body']}"
        )

    with subtests.test("Test build_mermaid_from_yaml, TD"):
        graph = build_mermaid_from_yaml(pipeline_config_path, direction="TD")
        assert (
            graph
            == f"{rendered_pipeline['header']['TD']}\n{rendered_pipeline['body']}"
        )

    with subtests.test("Test build_mermaid_from_yaml, LR + legend"):
        graph = build_mermaid_from_yaml(
            pipeline_config_path, direction="LR", legend=True
        )
        assert (
            graph == f"{rendered_pipeline['header']['LR']}\n"
            f"{rendered_pipeline['body']}{rendered_pipeline['legend']}\n"
        )


def test_render_graph_in_browser(
    tmpdir: py.path.local,
    pipeline_config_path: str,
    mock_webbrowser: pytest.MonkeyPatch,
) -> None:
    """Test rendering graph in browser.

    We use a temporary directory as the current working directory to avoid
    polluting the source tree. We also mock the webbrowser module to avoid
    opening a browser window during testing.
    """
    with tmpdir.as_cwd():
        render_graph_in_browser(build_mermaid_from_yaml(pipeline_config_path))

    assert tmpdir.join("mermaid.html").exists()
