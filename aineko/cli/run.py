# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline from the command line."""
from typing import Optional

from aineko.core.runner import Runner


def main(
    project: str,
    pipeline: str,
    conf_source: Optional[str] = None,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        project: Name of the project to run the pipeline for.
        pipeline: Name of the pipeline to run.
        conf_source: Path to the directory containing the configuration files.
        test_mode: Whether to run in test mode. (default: False)
    """
    runner = Runner(project=project, pipeline=pipeline, conf_source=conf_source)
    runner.run()
