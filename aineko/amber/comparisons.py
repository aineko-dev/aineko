# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Comparison functions for alert triggers."""
from typing import Dict, Union


def greater_than(
    value: Union[float, int], params: Dict[str, Union[float, int]]
) -> bool:
    """Check if metric value is greater than threshold.

    Args:
        value: Metric value
        params: Input parameters of the form {"threshold": Union[float, int]}

    Returns:
        bool: Whether the metric value is greater than the threshold.

    Raises:
        ValueError: If threshold is not specified in params.
    """
    if "threshold" not in params:
        raise ValueError("Threshold not specified in params.")
    return float(value) > float(params["threshold"])
