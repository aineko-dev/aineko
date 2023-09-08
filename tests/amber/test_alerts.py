# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Test Amber alerts nodes."""
from aineko.amber.alerts import Alerts


# pylint: disable=no-member
def test_alerts_node():
    """Test alerts node."""

    metrics_in = [
        {
            "metric": "LoggingLevelCounts",
            "value": 10,
            "metadata": {"level": "error"},
        },
        {
            "metric": "LoggingLevelCounts",
            "value": 10,
            "metadata": {"level": "warning"},
        },
        {
            "metric": "NodeHeartbeatInterval",
            "value": 10,
            "metadata": {"level": "warning"},
        },
        {
            "metric": "PipelineHeartbeatInterval",
            "value": 10,
            "metadata": {"level": "warning"},
        },
    ]

    alerts_out = [
        "greater_than alert triggered for metric LoggingLevelCounts",
        "greater_than alert triggered for metric LoggingLevelCounts",
        "greater_than alert triggered for metric NodeHeartbeatInterval",
        "greater_than alert triggered for metric PipelineHeartbeatInterval",
    ]

    alerts = Alerts(test=True)
    alerts.setup_test(inputs={"metrics": metrics_in}, outputs=["alerts"])
    outputs = alerts.run_test()

    for alert, expected in zip(outputs["alerts"], alerts_out):
        assert alert["message"] == expected
