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


class LOCAL_KAFKA_CONFIG(DEFAULT_KAFKA_CONFIG):
    """Kafka configuration."""

    REPORTING_DATASET = "reporting_local"
    DATASETS = [REPORTING_DATASET]


class AMBER_KAFKA_CONFIG(DEFAULT_KAFKA_CONFIG):
    """Kafka configuration."""

    # Amber Kafka broker settings
    # Amber broker server
    BROKER_SERVER = os.environ.get(
        "KAFKA_CONFIG_AMBER_BROKER", "localhost:9092"
    )
    # Config for amber kafka broker (remote logging / monitoring)
    BROKER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
    }
    # Config for amber kafka consumer
    CONSUMER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
        "auto.offset.reset": "earliest",
    }
    # Config for amber kafka producer
    PRODUCER_CONFIG = {
        "bootstrap.servers": BROKER_SERVER,
    }
    # Amber dataset config
    DATASET_PARAMS = {
        # One single partition for each dataset
        "num_partitions": 1,
        # No replication
        "replication_factor": 1,
        "config": {
            # Keep messages for 1 day
            "retention.ms": 1000
            * 60
            * 60
            * 24
            * 1,
        },
    }
    LOGGING_DATASET = "logging"
    REPORTING_DATASET = "reporting"
    DATASETS = [LOGGING_DATASET, REPORTING_DATASET]


class TESTING_NODE_CONFIG(BaseConfig):
    """Testing node configuration."""

    DATASETS = AMBER_KAFKA_CONFIG.get("DATASETS")


class AINEKO_CONFIG(BaseConfig):
    """Aineko configuration."""

    # Port to expose metrics
    RAY_METRICS_PORT = 8080

    # Aineko monitoring config
    HEARTBEAT_INTERVAL = 1

    # Timeout in seconds for dataset creation
    DATASET_CREATION_TIMEOUT = 300

    CONF_SOURCE = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf")
    )
    MSG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    KAFKA_STREAM_TYPE = "kafka_stream"

    # Default cpu for each node
    DEFAULT_NUM_CPUS = 0.5

    # Amber project dir name
    AMBER_PROJECT_DIR = "amber"

    # Amber conf dir path
    AMBER_CONF_SOURCE = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "amber/conf")
    )

    # Default Amber alert triggers
    AMBER_ALERT_TRIGGERS = {
        "log_errors": {
            "metric": "LoggingLevelCounts",
            "func": "aineko.amber.comparisons.greater_than",
            "params": {"threshold": 1},
            "metadata_filter": {
                "level": "error",
            },
        },
        "log_warnings": {
            "metric": "LoggingLevelCounts",
            "func": "aineko.amber.comparisons.greater_than",
            "params": {"threshold": 3},
            "metadata_filter": {
                "level": "warning",
            },
        },
        "node_heartbeat": {
            "metric": "NodeHeartbeatInteval",
            "func": "aineko.amber.comparisons.greater_than",
            "params": {"threshold": 60},
        },
        "pipeline_heartbeat": {
            "metric": "PipelineHeartbeatInterval",
            "func": "aineko.amber.comparisons.greater_than",
            "params": {"threshold": 60},
        },
    }


class AWS_CONFIG(BaseConfig):
    """AWS configuration."""

    # Needs to be in descending order of preference (cost)
    EC2_SPEC = {
        "m5.large": {"mem": 8, "vcpu": 2},
        "m5.xlarge": {"mem": 16, "vcpu": 4},
        "m5.2xlarge": {"mem": 32, "vcpu": 8},
        "m5.4xlarge": {"mem": 64, "vcpu": 16},
    }
