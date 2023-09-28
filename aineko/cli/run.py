# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline from the command line."""
from typing import Optional

from aineko.core.runner import Runner


def main(
    pipeline_config_file: str,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        pipeline_config_file: Path to the file containing the pipeline config
    """
    runner = Runner(pipeline_config_file=pipeline_config_file)
    runner.run()
