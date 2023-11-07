# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline from the command line."""
import logging
import time
import traceback
from typing import Optional

import click

from aineko.core.runner import Runner

logger = logging.getLogger(__name__)


@click.command()
@click.argument("pipeline-config-file")
@click.option(
    "-p",
    "--pipeline-name",
    help="Name of the pipeline to run.",
)
@click.option(
    "-r",
    "--retry",
    is_flag=True,
    help="Retry running the pipeline on failure.",
)
def run(
    pipeline_config_file: str,
    pipeline_name: Optional[str] = None,
    retry: bool = False,
) -> None:
    """Main function to run a pipeline from the command line.\f

    Args:
        pipeline_config_file: Path to the file containing the pipeline config
        pipeline_name: Name of the pipeline to run, overrides pipeline config
        retry: If true, retry running the pipeline on failure every 10 seconds
    """
    logger.info("Application is starting.")
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
                logger.error("Error running pipeline: %s", e)
                logger.debug(traceback.format_exc())
                time.sleep(10)
                continue
