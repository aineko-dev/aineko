# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""IO utilities."""
from typing import Union

import yaml


def load_yaml(file_path: str) -> dict:
    """Load yaml file into a dictionary.

    Args:
        file_path: path to yaml file

    Returns:
        dictionary of yaml file
    """
    with open(file_path, "r", encoding="utf-8") as conf_file:
        contents = yaml.safe_load(conf_file)
    if not contents:
        raise ValueError(f"YAML file {file_path} cannot be loaded.")
    return contents


def load_yamls(file_paths: Union[str, list]) -> dict:
    """Load yaml file(s) into a dictionary.

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
        yaml_dict.update(load_yaml(file_path))
    return yaml_dict
