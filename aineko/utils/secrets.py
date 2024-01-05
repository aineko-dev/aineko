# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Secrets utilities."""

import os
import re
from typing import Any, Dict, List


def _str_inject_secrets(str_: str) -> str:
    """Inject secrets from environment into a str."""
    secret_pattern = r"\{\$.*?\}"
    secret_match = re.search(secret_pattern, str_, re.DOTALL)
    if not secret_match:
        return str_
    else:
        secret_env_str = secret_match.group()
        secret_v = os.getenv(secret_env_str[2:][:-1], default=None)
        if secret_v is None:
            raise ValueError(
                "Failed to inject secret. "
                f"Environment variable {secret_env_str[2:][:-1]} not found."
            )
        str_ = str_.replace(secret_env_str, secret_v)
        return _str_inject_secrets(str_)


def _dict_inject_secrets(dict_: Dict[str, Any]) -> Dict[str, Any]:
    """Inject secrets from environment into a dict."""
    for k, v in list(dict_.items()):
        if isinstance(v, str):
            dict_[k] = _str_inject_secrets(v)
        elif isinstance(v, dict):
            dict_[k] = _dict_inject_secrets(v)
        elif isinstance(v, list):
            dict_[k] = _list_inject_secrets(v)
    return dict_


def _list_inject_secrets(list_: List[Any]) -> List[Any]:
    """Inject secrets from environment into a list."""
    for i, v in enumerate(list_):
        if isinstance(v, str):
            list_[i] = _str_inject_secrets(v)
        elif isinstance(v, dict):
            list_[i] = _dict_inject_secrets(v)
        elif isinstance(v, list):
            list_[i] = _list_inject_secrets(v)
    return list_


def inject_secrets(obj: Any) -> Any:
    """Inject secrets from environment into an object.

    This function is used by an aineko node to inject secrets into objects
    passed in to node params via a pipeline config.

    Given an object, inject secrets from the environment into the object
    recursively. Secrets are identified in strings by the pattern 
    {$SECRET_NAME} where SECRET_NAME is the name of the environment variable 
    to inject. For example, given the following environment variables:

    ```
    $ export SECRET1=secret1
    $ export SECRET2=secret2
    ```

    The following string:
    
    ```
    "This is a string with a {$SECRET1} and a {$SECRET2}."
    ```
    
    Would be transformed to:
    
    ```
    "This is a string with a secret1 and a secret2."
    ```

    This function supports injecting secrets into str, dict, and list objects.
    """
    if obj is None:
        return None
    if isinstance(obj, str):
        return _str_inject_secrets(obj)
    elif isinstance(obj, dict):
        return _dict_inject_secrets(obj)
    elif isinstance(obj, list):
        return _list_inject_secrets(obj)
    else:
        raise ValueError(
            "Failed to inject secrets. "
            f"Object type {type(obj)} not supported. "
            "Supported types are str, dict, and list."
        )
