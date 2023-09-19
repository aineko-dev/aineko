"""Module to run a pipeline from the command line."""
from typing import Optional

from aineko.core.runner import Runner


def main(
    pipeline_config_file: str,
    pipeline: Optional[str] = None,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        pipeline_config_file: Path to the file containing the pipeline config
        pipeline: Name of the pipeline to run
    """
    runner = Runner(
        pipeline_config_file=pipeline_config_file, pipeline=pipeline
    )
    runner.run()
