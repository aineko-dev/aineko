# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline from the command line."""
from typing import Optional

from aineko.core.runner import Runner


def main(
    pipeline_config_file: str,
    pipeline_name: Optional[str] = None,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        pipeline_config_file: Path to the file containing the pipeline config
        pipeline_name: Name of the pipeline to run, overrides pipeline config
    """
    runner = Runner(
        pipeline_config_file=pipeline_config_file, pipeline_name=pipeline_name
    )
    runner.run()
