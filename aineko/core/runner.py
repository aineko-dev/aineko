# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Module to run a pipeline."""
import time
from typing import Optional

import ray
from confluent_kafka.admin import AdminClient, NewTopic

from aineko.config import AINEKO_CONFIG, AMBER_KAFKA_CONFIG, LOCAL_KAFKA_CONFIG
from aineko.core.config_loader import ConfigLoader
from aineko.utils import imports


class Runner:
    """Runner class orchestrates the loading of config.

    Creates the datasets and starts the Ray nodes.

    Args:
        project (str): Name of the project
        pipeline (str): Name of the pipeline
        conf_source (str): Path to conf directory
        local_config (dict): Config for local kafka broker
        amber_config (dict): Config for Amber kafka broker

    Attributes:
        project (str): Name of the project
        pipeline (str): Name of the pipeline
        conf_source (str): Path to conf directory
        local_config (dict): Config for local kafka broker
        amber_config (dict): Config for Amber kafka broker
    """

    def __init__(
        self,
        project: str,
        pipeline: str,
        conf_source: Optional[str] = None,
        local_config: dict = LOCAL_KAFKA_CONFIG.get("BROKER_CONFIG"),
        amber_config: dict = AMBER_KAFKA_CONFIG.get("BROKER_CONFIG"),
    ):
        """Initializes the runner class."""
        self.project = project
        self.pipeline = pipeline
        self.conf_source = conf_source
        self.local_config = local_config
        self.amber_config = amber_config

    def run(self) -> None:
        """Runs the pipeline.

        Step 1: Load config for pipeline

        Step 2: Set up dataset for each edge

        Step 3: Set up nodes (including Node Manager) and run
        """
        # Step 1: load pipeline config
        pipeline_config = self.load_pipeline_config()

        # Step 2: Create the necessary datasets
        self.prepare_datasets(pipeline_config=pipeline_config)

        # Step 3: Create and execute each node
        self.run_nodes(pipeline_config=pipeline_config)

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
        local_kafka_client = AdminClient(self.local_config)
        amber_kafka_client = AdminClient(self.amber_config)

        # Fail if reserved amber dataset names are defined in catalog
        for reserved_dataset in AMBER_KAFKA_CONFIG.get("DATASETS"):
            if reserved_dataset in pipeline_config["catalog"]:
                raise ValueError(
                    f"Dataset {reserved_dataset} is reserved for Amber "
                    "(remote logging / monitoring service)."
                )

        # Add Amber logging dataset to catalog
        pipeline_config["catalog"][
            AMBER_KAFKA_CONFIG.get("LOGGING_DATASET")
        ] = {
            "type": AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"),
            "params": AMBER_KAFKA_CONFIG.get("DATASET_PARAMS"),
            "remote": True,
        }
        # Add Amber reporting dataset to catalog
        pipeline_config["catalog"][
            AMBER_KAFKA_CONFIG.get("REPORTING_DATASET")
        ] = {
            "type": AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"),
            "params": AMBER_KAFKA_CONFIG.get("DATASET_PARAMS"),
            "remote": True,
        }
        # Add local reporting dataset to catalog
        pipeline_config["catalog"][
            LOCAL_KAFKA_CONFIG.get("REPORTING_DATASET")
        ] = {
            "type": AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"),
            "params": LOCAL_KAFKA_CONFIG.get("DATASET_PARAMS"),
            "remote": False,
        }

        # Create all dataset defined in the catalog
        local_dataset_list = []
        amber_dataset_list = []
        for dataset_name, dataset_config in pipeline_config["catalog"].items():
            print(f"Creating dataset: {dataset_name}: {dataset_config}")
            # Create dataset for kafka streams
            if dataset_config["type"] == AINEKO_CONFIG.get("KAFKA_STREAM_TYPE"):
                # Set dataset parameters
                dataset_params = dataset_config.get(
                    "params", LOCAL_KAFKA_CONFIG.get("DATASET_PARAMS")
                )
                for param in [
                    "num_partitions",
                    "replication_factor",
                    "config",
                ]:
                    if param not in dataset_params:
                        dataset_params[param] = LOCAL_KAFKA_CONFIG.get(
                            "DATASET_PARAMS"
                        ).get(param)

                # Configure dataset
                new_dataset = NewTopic(
                    topic=dataset_name,
                    num_partitions=dataset_params.get("num_partitions"),
                    replication_factor=dataset_params.get("replication_factor"),
                    config=dataset_params.get("config"),
                )

                # Add dataset to appropriate list
                if dataset_config.get("remote", False):
                    amber_dataset_list.append(new_dataset)
                else:
                    local_dataset_list.append(new_dataset)

            else:
                raise ValueError(
                    "Unknown dataset type. Expected: "
                    f"{AINEKO_CONFIG.get('STREAM_TYPES')}."
                )

        # Create all configured datasets
        datasets = amber_kafka_client.create_topics(amber_dataset_list)
        if local_dataset_list:
            datasets.update(
                local_kafka_client.create_topics(local_dataset_list)
            )

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

    def run_nodes(self, pipeline_config: dict) -> list:
        """Runs the nodes for a given pipeline using Ray.

        Args:
            pipeline_config: pipeline configuration

        Returns:
            list: list of ray objects
        """
        # Initialize ray cluster
        ray.init(
            namespace=self.pipeline,
            _metrics_export_port=AINEKO_CONFIG.get("RAY_METRICS_PORT"),
        )

        # Run each node and collect result futures
        results = []
        actors = []

        default_node_config = pipeline_config.get("default_node_params", {})

        for node_name, node_config in pipeline_config["nodes"].items():
            # 1. Initalize actor
            # Extract the target class for a given node
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
            wrapped_class.options(**actor_params).remote()
            running_class = wrapped_class.remote()
            actors.append(running_class)

            # 2. Setup input and output datasets, incl logging and reporting
            outputs = node_config.get("outputs", [])
            outputs.extend(AMBER_KAFKA_CONFIG.get("DATASETS"))
            outputs.extend(LOCAL_KAFKA_CONFIG.get("DATASETS"))
            print(
                f"Running {node_name} node on {self.pipeline} pipeline: "
                f"inputs={node_config.get('inputs', None)}, "
                f"outputs={outputs}"
            )
            running_class.setup_datasets.remote(
                inputs=node_config.get("inputs", None),
                outputs=outputs,
                catalog=pipeline_config["catalog"],
                node=node_name,
                pipeline=self.pipeline,
                project=self.project,
            )

            # 3. Execute the node
            results.append(
                running_class.execute.remote(
                    params=node_config.get("class_params", None)
                )
            )

        return ray.get(results)
