"""Utils to create a aineko pipeline from existing templates."""

import os

from cookiecutter.main import cookiecutter


def create_pipeline_directory() -> None:
    """Creates boilerplate code and config required for an Aineko pipeline."""
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # Assumes that aineko_core is always 2-levels above this file
    # While this assumption is somewhat fragile, we most likely
    # will not have to pass this path for long after aineko pkg goes public
    aineko_core_directory = os.path.dirname(os.path.dirname(script_directory))
    # assumes templates is a folder that is one-level up
    templates_directory = f"{os.path.dirname(script_directory)}/templates"
    # Only one type of pipeline, hence this argument is no-arg
    cookiecutter(
        f"{templates_directory}/simple_pipeline",
        extra_context={"aineko_core_dir": aineko_core_directory},
    )
