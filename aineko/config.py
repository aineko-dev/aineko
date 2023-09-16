"""Configuration file for Aineko modules."""
import copy
import os
from typing import Any


# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
class BaseConfig:
    """Base Config."""

    @classmethod
    def get(cls, attribute: str) -> Any:
        """Returns the base config."""
        if hasattr(cls, attribute):
            return copy.deepcopy(getattr(cls, attribute))
        raise ValueError(f"{attribute} not found in {cls.__name__}")


class DEFAULT_KAFKA_CONFIG(BaseConfig):
    """Kafka configuration."""

    # Default Kafka broker settings
    # Default broker server
    BROKER_SERVER = os.environ.get("KAFKA_CONFIG_BROKER", "localhost:9092")
    # Config for default kafka broker
    BROKER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
    }
    # Config for default kafka consumer
    CONSUMER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
        "auto.offset.reset": "earliest",
    }
    # Config for default kafka producer
    PRODUCER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
    }
    # Default dataset config
    DATASET_PARAMS = {
        # One single partition for each dataset
        "num_partitions": 1,
        # No replication
        "replication_factor": 1,
        "config": {
            # Keep messages for 7 days
            "retention.ms": 1000
            * 60
            * 60
            * 24
            * 7,
        },
    }

    # Default Kafka consumer settings
    # Timeout for kafka consumer polling (seconds)
    CONSUMER_TIMEOUT = 0
    # Max number of messages to retreive when getting the last message
    CONSUMER_MAX_MESSAGES = 1000000
    # Consumer overridables
    # See: https://kafka.apache.org/documentation/#consumerconfigs
    CONSUMER_OVERRIDABLES = ["auto.offset.reset"]

    # Default Kafka producer settings
    # Producer overridables
    # See: https://kafka.apache.org/documentation/#producerconfigs
    # Empty list means no overridable settings
    PRODUCER_OVERRIDABLES = []  # type: ignore

    # Default datasets to create for every pipeline
    LOGGING_DATASET = "logging"
    DATASETS = [LOGGING_DATASET]


class TESTING_NODE_CONFIG(BaseConfig):
    """Testing node configuration."""

    DATASETS = DEFAULT_KAFKA_CONFIG.get("DATASETS")


class AINEKO_CONFIG(BaseConfig):
    """Aineko configuration."""

    # Port to expose metrics
    RAY_METRICS_PORT = 8080

    # Aineko monitoring config
    HEARTBEAT_INTERVAL = 1

    # Timeout in seconds for dataset creation
    DATASET_CREATION_TIMEOUT = 300

    DEFAULT_PIPELINE_CONFIG = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "conf/pipelines.yml"
        )
    )
    MSG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    KAFKA_STREAM_TYPE = "kafka_stream"

    # Default cpu for each node
    DEFAULT_NUM_CPUS = 0.5

    # Valid log levels
    LOG_LEVELS = ("info", "debug", "warning", "error", "critical")


class NODE_MANAGER_CONFIG(BaseConfig):
    """Node Manager configuration."""

    # Name to call node
    NAME = "node_manager"

    # Ray options for NodeManager
    RAY_OPTIONS = {
        "num_cpus": 0.1,
    }

    # Node config
    NODE_CONFIG = {
        "class": "aineko.core.node_manager.NodeManager",
    }
