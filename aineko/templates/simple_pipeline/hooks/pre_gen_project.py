"""A series of cookiecutter pre-codegen hooks to validate user input.

These code will run after user-input is provided and before files are
generated.

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""
import os
import re
import sys

# Color codes for logging
ERROR = "\x1b[1;31m[ERROR]: "
TERMINATOR = "\x1b[0m"

MODULE_REGEX = r"^[_a-zA-Z][_a-zA-Z0-9]+$"

project_slug = "{{ cookiecutter.project_slug }}"
pipeline_slug = "{{ cookiecutter.pipeline_slug }}"
aineko_core_directory = "{{ cookiecutter._aineko_core_directory }}"


class AinekoPathValidationException(Exception):
    """Exception when validation of user-provided path does not point to valid aineko-core repo."""

    pass


def validate_slug(slug: str) -> None:
    """Validate a slug to ensure it only contains lowercase letters, dashes, and underscores.

    Args:
        slug (str): The slug to be validated.

    Raises:
        ValueError: If the slug contains invalid characters.
    """
    if not re.match(r"^[a-z_-]+$", slug):
        raise ValueError(
            f"[{slug}] Slug can only contain lowercase letters, dashes, and underscores."
        )


def validate_aineko_core_dir(aineko_dir: str) -> None:
    """Validate the existence and content of the 'aineko_core' directory.

    Args:
        aineko_dir (str): The path to the 'aineko_core' directory.

    Raises:
        DirectoryValidationException: If the directory is empty or is empty.
    """
    if os.path.exists(aineko_dir) and os.path.isdir(aineko_dir):
        # 1. Check if the directory is legit and if there are files inside the directory
        file_list = os.listdir(aineko_dir)
        if len(file_list) == 0:
            raise AinekoPathValidationException("The directory is empty.")

        # 2. Check if the directory path ends with '/aineko_core'
        if not aineko_dir.endswith("/aineko-core"):
            raise AinekoPathValidationException(
                "The directory path does not end with '/aineko-core'."
            )
    else:
        raise AinekoPathValidationException(
            f"The directory '{aineko_dir}' does not exist or is not a directory."
        )


try:
    validate_slug(project_slug)
    validate_slug(pipeline_slug)
    # This is a stop-gap. In future, we will not need to refer
    # to a local version of aineko_core for generated pipelines
    validate_aineko_core_dir(aineko_core_directory)

except ValueError as ex:
    print(ERROR + str(ex) + TERMINATOR)
    sys.exit(1)

except AinekoPathValidationException as ex:
    print(ERROR + str(ex) + TERMINATOR)
    sys.exit(1)
