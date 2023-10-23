# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A wrapper class that executes Docker CLI commands via subprocess."""
import subprocess


class DockerCLIWrapper:
    """A wrapper class that executes Docker CLI commands via subprocess.

    This class provides methods to start, stop, and restart Docker services
    using docker-compose.

    Methods:
        start_service(cls) -> None:
            Start the Docker service.

        stop_service(cls) -> None:arg
            Stop the running Docker service.

        restart_service(cls) -> None:
            Restart the running Docker service.
    """

    _docker_compose_config = """
version: "3"
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.0
    hostname: zookeeper
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  broker:
    image: confluentinc/cp-kafka:7.3.0
    container_name: broker
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper:2181"
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://broker:29092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
"""

    @classmethod
    def start_service(cls) -> None:
        """Start the Docker service."""
        try:
            output = subprocess.check_output(
                args="docker-compose -f - up -d",
                input=cls._docker_compose_config,
                shell=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")

    @classmethod
    def stop_service(cls) -> None:
        """Stop the running Docker service."""
        try:
            output = subprocess.check_output(
                args="docker-compose -f - stop",
                input=cls._docker_compose_config,
                shell=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")

    @classmethod
    def restart_service(cls) -> None:
        """Restart the running Docker service."""
        try:
            output = subprocess.check_output(
                args="docker-compose -f - restart",
                input=cls._docker_compose_config,
                shell=True,
                text=True,
                stderr=subprocess.STDOUT,
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")
