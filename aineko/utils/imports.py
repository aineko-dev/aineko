# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Import utilities."""
import importlib
import inspect
from typing import Any, Optional


def import_from_string(  # type: ignore[no-untyped-def]
    attr: str,
    kind: str,
    reqd_params: Optional[list] = None,
    ret_type: Optional[Any] = None,
):
    """Get a function from a string.

    Args:
        attr: String to import (e.g. ...module.function or ...module.Class)
        kind: Kind of object to import (function or class)
        reqd_params: Required parameters of a function or class
        ret_type: Return type of a function (ignored if kind is class)

    Returns:
        imported_func: Imported function

    Raises:
        AttributeError: If attr does not exist
        ValueError: If kind is not a valid kind
        ValueError: If attr is not in the correct format
        ValueError: If attr is not a function
        ValueError: If attr is not a class
    """
    # Check if kind is valid
    if kind not in ["function", "class"]:
        raise ValueError(
            f"Kind {kind} is not a valid kind. "
            "Valid kinds are 'function' and 'class'."
        )

    # Check if attribute is in the correct format
    if "." not in attr:
        raise ValueError(
            f"Attribute {attr} must be in the format "
            "...module.function or ...module.Class"
        )

    # Import attribute from module
    module_name, attr_name = attr.rsplit(".", 1)
    module = importlib.import_module(module_name)
    imported_attr = getattr(module, attr_name)

    # Validate attribute
    if kind == "function":
        if not inspect.isfunction(imported_attr):
            raise ValueError(
                f"Attribute {imported_attr} is {type(imported_attr)}. "
                "Expected a function."
            )

    elif kind == "class":
        if not inspect.isclass(imported_attr):
            raise ValueError(
                f"Attribute {imported_attr} is {type(imported_attr)}. "
                "Expected a class."
            )

    # Check if required parameters are present
    if isinstance(reqd_params, list):
        for param in reqd_params:
            if param not in inspect.signature(imported_attr).parameters:
                raise ValueError(
                    f"Imported function {imported_attr} "
                    f"does not have a {param} parameter."
                )

    # Check if returned type is correct
    if isinstance(ret_type, str):
        imported_attr_type = inspect.signature(imported_attr).return_annotation
        if imported_attr_type != ret_type:
            raise ValueError(
                f"Imported function {imported_attr} returns "
                f"{imported_attr_type}. Expected {ret_type}."
            )

    return imported_attr
