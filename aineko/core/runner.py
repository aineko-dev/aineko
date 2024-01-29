# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Submodule that handles the running of a pipeline from config."""
import logging
import time
from typing import Dict, Optional

import ray
from confluent_kafka.admin import AdminClient, NewTopic  # type: ignore

from aineko.config import (
    AINEKO_CONFIG,
    DEFAULT_KAFKA_CONFIG,
    NODE_MANAGER_CONFIG,
)
from aineko.core.config_loader import ConfigLoader
from aineko.core.node import PoisonPill
from aineko.models.config_schema import Config
from aineko.utils import imports

logger = logging.getLogger(__name__)


class Runner:
    """Runs the pipeline described in the config.

    Args:
        pipeline_config_file (str): Path to pipeline config file
        pipeline_name (str): Name of the pipeline
        kafka_config (dict): Config for kafka broker
        dataset_prefix (Optional[str]): Prefix for dataset names.
            Kafka topics will be called `<prefix>.<pipeline>.<dataset_name>`.

    Attributes:
        pipeline_config_file (str): Path to pipeline config file
        pipeline_name (str): Name of the pipeline, overrides pipeline config
        kafka_config (dict): Config for kafka broker
        pipeline_name (str): Name of the pipeline, loaded from config
        dataset_prefix (Optional[str]): Prefix for dataset names
    """

    def __init__(
        self,
        pipeline_config_file: str,
        pipeline_name: Optional[str] = None,
        kafka_config: dict = DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG"),
        metrics_export_port: int = AINEKO_CONFIG.get("RAY_METRICS_PORT"),
        dataset_prefix: Optional[str] = None,
    ):
        """Initializes the runner class."""
        self.pipeline_config_file = pipeline_config_file
        self.kafka_config = kafka_config
        self.metrics_export_port = metrics_export_port
        self.pipeline_name = pipeline_name
        self.dataset_prefix = dataset_prefix or ""

    def run(self) -> None:
        """Runs the pipeline.

        Step 1: Load config for pipeline

        Step 2: Set up datasets

        Step 3: Set up PoisonPill node that is available to all nodes

        Step 4: Set up nodes (including Node Manager)
        """
        # Load pipeline config
        pipeline_config = self.load_pipeline_config()
        self.pipeline_name = self.pipeline_name or pipeline_config.name

        # Create the necessary datasets
        self.prepare_datasets(
            config=pipeline_config.datasets,
            user_dataset_prefix=self.pipeline_name,
        )

        # Initialize ray cluster
        ray.shutdown()
        ray.init(
            namespace=self.pipeline_name,
            _metrics_export_port=self.metrics_export_port,
        )

        # Create poison pill actor
        poison_pill = ray.remote(PoisonPill).remote()

        # Add Node Manager to pipeline config
        pipeline_config.nodes[
            NODE_MANAGER_CONFIG.get("NAME")
        ] = Config.Pipeline.Node(**NODE_MANAGER_CONFIG.get("NODE_CONFIG"))

        # Create each node (actor)
        results = self.prepare_nodes(
            pipeline_config=pipeline_config,
            poison_pill=poison_pill,  # type: ignore
        )

        ray.get(results)

    def load_pipeline_config(self) -> Config.Pipeline:
        """Loads the config for a given pipeline.

        Returns:
            pipeline config
        """
        config = ConfigLoader(
            pipeline_config_file=self.pipeline_config_file,
        ).load_config()

        return config.pipeline

    def prepare_datasets(
        self,
        config: Dict[str, Config.Pipeline.Dataset],
        user_dataset_prefix: Optional[str] = None,
    ) -> bool:
        """Creates the required datasets for a given pipeline.

        Datasets can be configured using the `params` key, using config keys
        found in: https://kafka.apache.org/documentation.html#topicconfigs

        Args:
            config: dataset configuration found in pipeline config
                Should follow the schema below:
                ```python
                    {
                        "dataset_name": {
                            "type": str ("kafka_stream"),
                            "params": dict
                    }
                ```
            user_dataset_prefix: prefix only for datasets defined by the user.
                i.e. `<prefix>.<user_dataset_prefix>.<dataset_name>`

        Returns:
            True if successful

        Raises:
            ValueError: if dataset "logging" is defined in the catalog
        """
        # Connect to kafka cluster
        kafka_client = AdminClient(self.kafka_config)

        # Add prefix to user defined datasets
        if user_dataset_prefix:
            config = {
                f"{user_dataset_prefix}.{dataset_name}": dataset_config
                for dataset_name, dataset_config in config.items()
            }

        # Fail if reserved dataset names are defined in catalog
        for reserved_dataset in DEFAULT_KAFKA_CONFIG.get("DATASETS"):
            if reserved_dataset in config:
                raise ValueError(
                    f"Unable to create dataset `{reserved_dataset}`. "
                    "Reserved for internal use."
                )

        # Add logging dataset to catalog
        config[
            DEFAULT_KAFKA_CONFIG.get("LOGGING_DATASET")
        ] = Config.Pipeline.Dataset(
            type=AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"),
            params=DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
        )

        # Create all dataset defined in the catalog
        dataset_list = []
        for dataset_name, dataset_config in config.items():
            logger.info(
                "Creating dataset: %s: %s", dataset_name, dataset_config
            )
            # Create dataset for kafka streams
            if dataset_config.type == AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"):
                # User defined
                if not dataset_config.params:
                    dataset_config.params = {}

                dataset_params = {
                    **DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
                    **dataset_config.params,
                }

                # Configure dataset
                if self.dataset_prefix:
                    topic_name = f"{self.dataset_prefix}.{dataset_name}"
                else:
                    topic_name = dataset_name

                new_dataset = NewTopic(
                    topic=topic_name,
                    num_partitions=dataset_params.get("num_partitions"),
                    replication_factor=dataset_params.get("replication_factor"),
                    config=dataset_params.get("config"),
                )

                # Add dataset to appropriate list
                dataset_list.append(new_dataset)

            else:
                raise ValueError(
                    "Unknown dataset type. Expected: "
                    f"{AINEKO_CONFIG.get('STREAM_TYPES')}."
                )

        # Create all configured datasets
        datasets = kafka_client.create_topics(dataset_list)

        # Block until all datasets finish creation
        cur_time = time.time()
        while True:
            if all(future.done() for future in datasets.values()):
                logger.info("All datasets created.")
                break
            if time.time() - cur_time > AINEKO_CONFIG.get(
                "DATASET_CREATION_TIMEOUT"
            ):
                raise TimeoutError(
                    "Timeout while creating Kafka datasets. "
                    "Please check your Kafka cluster."
                )

        return datasets

    def prepare_nodes(
        self,
        pipeline_config: Config.Pipeline,
        poison_pill: ray.actor.ActorHandle,
    ) -> list:
        """Prepare actor handles for all nodes.

        Args:
            pipeline_config: pipeline configuration

        Returns:
            dict: mapping of node names to actor handles
            list: list of ray objects

        Raises:
            ValueError: if error occurs while initializing actor from config
        """
        # Collect all  actor futures
        results = []
        if pipeline_config.default_node_settings:
            default_node_config = pipeline_config.default_node_settings
        else:
            default_node_config = {}

        for node_name, node_config in pipeline_config.nodes.items():
            if node_config.node_settings:
                node_settings = node_config.node_settings
            else:
                node_settings = {}
            # Initialize actor from specified class in config
            try:
                target_class = imports.import_from_string(
                    attr=node_config.class_name, kind="class"
                )
            except AttributeError as exc:
                raise ValueError(
                    "Invalid node class name specified in config for node '"
                    f"{node_name}'. Please check your config file at: "
                    f"{self.pipeline_config_file}\n"
                    f"Error: {exc}"
                ) from None

            actor_params = {
                **default_node_config,
                **node_settings,
                "name": node_name,
                "namespace": self.pipeline_name,
            }

            wrapped_class = ray.remote(target_class)
            wrapped_class.options(**actor_params)
            actor_handle = wrapped_class.remote(
                node_name=node_name,
                pipeline_name=self.pipeline_name,
                poison_pill=poison_pill,
            )

            if node_config.outputs:
                outputs = node_config.outputs
            else:
                outputs = []

            if node_config.inputs:
                inputs = node_config.inputs
            else:
                inputs = None
            # Setup input and output datasets

            actor_handle.setup_datasets.remote(
                inputs=inputs,
                outputs=outputs,
                datasets=pipeline_config.datasets,
                has_pipeline_prefix=True,
            )

            # Setup internal datasets like logging, without pipeline prefix
            actor_handle.setup_datasets.remote(
                outputs=DEFAULT_KAFKA_CONFIG.get("DATASETS"),
                datasets=pipeline_config.datasets,
            )

            # Create actor future (for execute method)
            results.append(
                actor_handle.execute.remote(params=node_config.node_params)
            )

        return results
