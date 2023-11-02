# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline from the command line."""
import time
import traceback
from typing import Optional

from aineko.core.runner import Runner


def main(
    pipeline_config_file: str,
    pipeline_name: Optional[str] = None,
    retry: bool = False,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        pipeline_config_file: Path to the file containing the pipeline config
        pipeline_name: Name of the pipeline to run, overrides pipeline config
        retry: If true, retry running the pipeline on failure every 10 seconds
    """
    while True:
        try:
            runner = Runner(
                pipeline_config_file=pipeline_config_file,
                pipeline_name=pipeline_name,
            )
            runner.run()
        except Exception as e:  # pylint: disable=broad-except
            if not retry:
                raise e
            else:
                print(f"Error running pipeline: {e}")
                print(traceback.format_exc())
                time.sleep(10)
                continue
