"""Test Amber metrics nodes."""
from aineko.amber.metrics import (
    LoggingLevelCounts,
    NodeHeartbeatInterval,
    PipelineHeartbeatInterval,
)

NUM_MESSAGES = 10


# pylint: disable=no-member
def test_node_heartbeat_node():
    """Test node heartbeat node."""
    interval = 0
    heartbeats_in = ["heartbeat"] * NUM_MESSAGES

    metric_out = [
        {
            "metric": "NodeHeartbeatInterval",
            "interval": interval,
            "metadata": {
                "source_pipeline": "test",
                "source_node": "test",
            },
        }
    ] * NUM_MESSAGES

    heartbeat_node = NodeHeartbeatInterval.__ray_actor_class__()
    heartbeat_node.enable_test_mode()
    heartbeat_node.setup_test(
        inputs={"heartbeats": heartbeats_in},
        outputs=["metrics"],
        params={
            "interval": interval,
            "source_pipeline": "test_pipieline",
            "source_node": "NodeHeartbeatInterval",
        },
    )
    outputs = heartbeat_node.run_test()
    for alert in outputs["metrics"]:
        for metric in metric_out:
            for key, value in metric.items():
                assert alert[key] == value


def test_pipeline_heartbeat_node():
    """Test pipeline heartbeat node."""

    interval = 0
    heartbeats_in = ["heartbeat"] * NUM_MESSAGES

    metric_out = [
        {
            "metric": "PipelineHeartbeatInterval",
            "interval": interval,
            "metadata": {"source_pipeline": "test"},
        }
    ] * NUM_MESSAGES

    heartbeat_node = PipelineHeartbeatInterval.__ray_actor_class__()
    heartbeat_node.enable_test_mode()
    heartbeat_node.setup_test(
        inputs={"heartbeats": heartbeats_in},
        outputs=["metrics"],
        params={
            "interval": interval,
            "source_pipeline": "test",
        },
    )
    outputs = heartbeat_node.run_test()
    for alert in outputs["metrics"]:
        for metric in metric_out:
            for key, value in metric.items():
                assert alert[key] == value


def test_logging_level_counts_node():
    """Test pipeline heartbeat node."""

    interval = 0
    logs_in = [
        {"level": "error"},
        {"level": "warning"},
        {"level": "info"},
        {"level": "debug"},
    ]

    metric_out = [
        {
            "metric": "LoggingLevelCounts",
            "interval": 0,
            "value": 1,
            "metadata": {"level": "error"},
        },
        {
            "metric": "LoggingLevelCounts",
            "interval": 0,
            "value": 1,
            "metadata": {"level": "warning"},
        },
        {
            "metric": "LoggingLevelCounts",
            "interval": 0,
            "value": 1,
            "metadata": {"level": "info"},
        },
        {
            "metric": "LoggingLevelCounts",
            "interval": 0,
            "value": 1,
            "metadata": {"level": "debug"},
        },
    ]

    log_level_node = LoggingLevelCounts.__ray_actor_class__()
    log_level_node.enable_test_mode()
    log_level_node.setup_test(
        inputs={"logs": logs_in},
        outputs=["metrics"],
        params={"interval": interval},
    )
    outputs = log_level_node.run_test()
    for metric in metric_out:
        assert metric in outputs["metrics"]
