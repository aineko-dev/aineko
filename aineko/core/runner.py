"""Submodule that handles the running of a pipeline from config."""
import time
from typing import Optional

import ray
from confluent_kafka.admin import AdminClient, NewTopic

from aineko.config import (
    AINEKO_CONFIG,
    DEFAULT_KAFKA_CONFIG,
    NODE_MANAGER_CONFIG,
)
from aineko.core.config_loader import ConfigLoader
from aineko.core.node import PoisonPill
from aineko.utils import imports


class Runner:
    """Runs the pipeline described in the config.

    Args:
        project (str): Name of the project
        pipeline (str): Name of the pipeline
        conf_source (str): Path to conf directory
        kafka_config (dict): Config for kafka broker

    Attributes:
        project (str): Name of the project
        pipeline (str): Name of the pipeline
        conf_source (str): Path to conf directory
        kafka_config (dict): Config for kafka broker
    """

    def __init__(
        self,
        project: str,
        pipeline: str,
        conf_source: Optional[str] = None,
        kafka_config: dict = DEFAULT_KAFKA_CONFIG.get("BROKER_CONFIG"),
    ):
        """Initializes the runner class."""
        self.project = project
        self.pipeline = pipeline
        self.conf_source = conf_source
        self.kafka_config = kafka_config

    def run(self) -> None:
        """Runs the pipeline.

        Step 1: Load config for pipeline

        Step 2: Set up datasets

        Step 3: Set up PoisonPill node that is available to all nodes

        Step 4: Set up nodes (including Node Manager)
        """
        # Load pipeline config
        pipeline_config = self.load_pipeline_config()

        # Create the necessary datasets
        self.prepare_datasets(pipeline_config=pipeline_config)

        # Initialize ray cluster
        ray.shutdown()
        ray.init(
            namespace=self.pipeline,
            _metrics_export_port=AINEKO_CONFIG.get("RAY_METRICS_PORT"),
        )

        # Create poison pill actor
        poison_pill = ray.remote(PoisonPill).remote()

        # Add Node Manager to pipeline config
        pipeline_config["nodes"][
            NODE_MANAGER_CONFIG.get("NAME")
        ] = NODE_MANAGER_CONFIG.get("NODE_CONFIG")

        # Create each node (actor)
        results = self.prepare_nodes(
            pipeline_config=pipeline_config,
            poison_pill=poison_pill,  # type: ignore
        )

        ray.get(results)

    def load_pipeline_config(self) -> dict:
        """Loads the config for a given pipeline and project.

        Returns:
            pipeline config
        """
        config = ConfigLoader(
            project=self.project, conf_source=self.conf_source
        ).load_config()
        return config[self.project][self.pipeline]

    def prepare_datasets(self, pipeline_config: dict) -> bool:
        """Creates the required datasets for a given pipeline.

        Args:
            config: pipeline_config configuration

        Returns:
            True if successful

        Raises:
            ValueError: if dataset "logging" is defined in the catalog
        """
        # Connect to kafka cluster
        kafka_client = AdminClient(self.kafka_config)

        # Fail if reserved dataset names are defined in catalog
        for reserved_dataset in DEFAULT_KAFKA_CONFIG.get("DATASETS"):
            if reserved_dataset in pipeline_config["catalog"]:
                raise ValueError(
                    f"Dataset {reserved_dataset} is reserved for internal use."
                )

        # Add logging dataset to catalog
        pipeline_config["catalog"][
            DEFAULT_KAFKA_CONFIG.get("LOGGING_DATASET")
        ] = {
            "type": AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"),
            "params": DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
        }

        # Create all dataset defined in the catalog
        dataset_list = []
        for dataset_name, dataset_config in pipeline_config["catalog"].items():
            print(f"Creating dataset: {dataset_name}: {dataset_config}")
            # Create dataset for kafka streams
            if dataset_config["type"] == AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"):
                # User defined
                dataset_params = {
                    **DEFAULT_KAFKA_CONFIG.get("DATASET_PARAMS"),
                    **dataset_config.get("params", {}),
                }

                # Configure dataset
                new_dataset = NewTopic(
                    topic=dataset_name,
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
                print("All datasets created.")
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
        self, pipeline_config: dict, poison_pill: ray.actor.ActorHandle
    ) -> list:
        """Prepare actor handles for all nodes.

        Args:
            pipeline_config: pipeline configuration

        Returns:
            dict: mapping of node names to actor handles
            list: list of ray objects
        """
        # Collect all  actor futures
        results = []

        default_node_config = pipeline_config.get("default_node_params", {})

        for node_name, node_config in pipeline_config["nodes"].items():
            # Initalize actor from specified class in config
            target_class = imports.import_from_string(
                attr=node_config["class"], kind="class"
            )
            actor_params = {
                **default_node_config,
                **node_config.get("node_params", {}),
                "name": node_name,
                "namespace": self.pipeline,
            }

            wrapped_class = ray.remote(target_class)
            wrapped_class.options(**actor_params)
            actor_handle = wrapped_class.remote(poison_pill=poison_pill)

            # Setup input and output datasets, incl logging
            outputs = node_config.get("outputs", [])
            outputs.extend(DEFAULT_KAFKA_CONFIG.get("DATASETS"))
            print(
                f"Running {node_name} node on {self.pipeline} pipeline: "
                f"inputs={node_config.get('inputs', None)}, "
                f"outputs={outputs}"
            )
            actor_handle.setup_datasets.remote(
                inputs=node_config.get("inputs", None),
                outputs=outputs,
                catalog=pipeline_config["catalog"],
                node=node_name,
                pipeline=self.pipeline,
                project=self.project,
            )

            # Create actor future (for execute method)
            results.append(
                actor_handle.execute.remote(
                    params=node_config.get("class_params", None)
                )
            )

        return results
