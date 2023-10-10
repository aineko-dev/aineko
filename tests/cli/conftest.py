# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test fixtures for cli.visualize."""

import os

import pytest


@pytest.fixture(scope="module")
def pipeline_config_path():
    """Pipeline config yml path."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "conf",
        "test_pipeline.yml",
    )


@pytest.fixture(scope="module")
def rendered_pipeline() -> dict:
    """A dictionary containing the rendered pipeline.

    Keys:
        header: has subkeys for LR and TD mermaid header
        body: mermaid body
        legend: mermaid legend
    """
    return {
        "header": {"LR": "flowchart LR", "TD": "flowchart TD"},
        "body": """classDef datasetClass fill:#87CEEB
classDef nodeClass fill:#eba487
N_sequencer((sequencer)):::nodeClass -->  T_integer_sequence[integer_sequence]:::datasetClass
N_sequencer((sequencer)):::nodeClass -->  T_env_var[env_var]:::datasetClass
T_integer_sequence[integer_sequence]:::datasetClass -->  N_doubler((doubler)):::nodeClass
N_doubler((doubler)):::nodeClass -->  T_integer_doubles[integer_doubles]:::datasetClass
""",
        "legend": """subgraph Legend
node((Node)):::nodeClass
dataset[Dataset]:::datasetClass
end""",
    }


@pytest.fixture(autouse=False)
def mock_webbrowser(monkeypatch: pytest.MonkeyPatch):
    """Mock native webbrowser."""

    def open(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "aineko.cli.visualize.webbrowser.open",
        open,
        raising=True,
    )
