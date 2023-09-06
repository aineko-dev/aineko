# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""IO utilities."""
from typing import Union

import yaml


def load_yamls(file_paths: Union[str, list]) -> dict:
    """Load yaml files into a dictionary.

    If multiple keys with the same name exist, the last one will be used.

    Args:
        file_paths: list of paths to yaml files

    Returns:
        dictionary of combined yaml files
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    yaml_dict = {}
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as conf_file:
            contents = yaml.safe_load(conf_file)
            if contents is not None:
                yaml_dict.update(contents)
    return yaml_dict
