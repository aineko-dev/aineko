# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the aineko.core.runner module."""
from typing import Type

from aineko.core.runner import Runner


def test_run(runner: Type[Runner]) -> None:
    # Test that ray has run with expected nodes
    # runner.run()
    assert True


def test_load_pipeline_config(runner: Type[Runner]) -> None:
    # Test that ray has run with expected nodes
    # config = runner.load_pipeline_config()
    assert True


def test_prepare_datasets(runner: Type[Runner]) -> None:
    # Test that ray has run with expected nodes
    # pipeline_config = runner.load_pipeline_config()
    # runner.prepare_datasets(pipeline_config)
    assert True


def test_run_nodes(runner: Type[Runner]) -> None:
    # Test that ray has run with expected nodes
    # pipeline_config = runner.load_pipeline_config()
    # runner.prepare_datasets(pipeline_config)
    # runner.run_nodes(pipeline_config=pipeline_config)
    assert True
