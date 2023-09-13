"""Module to run a pipeline from the command line."""
from typing import Optional

from aineko.core.runner import Runner


def main(
    pipeline: str,
    pipline_config_path: str, 
    catalog_config_path: str,
) -> None:
    """Main function to run a pipeline from the command line.

    Args:
        project: Name of the project to run the pipeline for.
        pipeline: Name of the pipeline to run.
        conf_source: Path to the directory containing the configuration files.
        test_mode: Whether to run in test mode. (default: False)
    """
    runner = Runner(pipeline=pipeline, pipline_config_path=pipline_config_path, catalog_config_path=catalog_config_path)
    # print("PROJECT: ", project)
    # print("PIPELINE: ", pipeline)
    runner.run()
