# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Secrets utilities."""

import os
from typing import Dict, Str, Any, Union
import re


def str_inject_secret(string: Union[str, None]) -> Union[str, None]:
    """Inject secrets from environment into a str."""
    if string is None:
        return None
    secret_pattern = r"{$.*?}"
    secret_match = re.search(secret_pattern, string, re.DOTALL)
    if not secret_match:
        return string
    else:
        secret_env_string = secret_match.group(1)
        secret_v = os.getenv(secret_env_string[1:][:-1], default=None)
        if secret_v is None:
            raise ValueError(
                "Failed to inject secret. "
                f"Environment variable {string} not found."
                )
        string.replace(secret_env_string, secret_v)
        str_inject_secret(string)

def dict_inject_secret(
        dictionary: Union[Dict[Str, Any], None]
        ) -> Union[Dict[Str, Any], None]:
    """Inject secrets from environment into a dict."""
    if dictionary is None:
        return None
    for k, v in dictionary.items():
        if isinstance(v, str):
            dictionary[k] = str_inject_secret(v)
        elif isinstance(v, dict):
            dictionary[k] = dict_inject_secret(v)
    return dictionary