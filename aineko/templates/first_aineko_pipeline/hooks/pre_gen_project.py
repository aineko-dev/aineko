# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
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

class AinekoPathValidationException(Exception):
    """Exception when validation of user-provided path does not point to valid aineko-core repo."""

    pass


def validate_slug(slug: str) -> None:
    """Validate a slug to ensure it only contains lowercase letters, dashes, and underscores.

    Args:
        slug: The slug to be validated.

    Raises:
        ValueError: If the slug contains invalid characters.
    """
    if not re.match(r"^[a-z_-]+$", slug):
        raise ValueError(
            f"[{slug}] Slug can only contain lowercase letters, dashes, and underscores."
        )


try:
    validate_slug(project_slug)
    validate_slug(pipeline_slug)


except ValueError as ex:
    print(ERROR + str(ex) + TERMINATOR)
    sys.exit(1)

except AinekoPathValidationException as ex:
    print(ERROR + str(ex) + TERMINATOR)
    sys.exit(1)
