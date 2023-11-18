# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A wrapper class that executes Docker CLI commands via subprocess."""
import subprocess
import sys
from typing import Optional

import click
from click.core import Context


class DockerCLIWrapper:
    """A wrapper class that executes Docker CLI commands via subprocess.

    This class provides methods to start, stop, and restart Docker services
    using docker-compose.

    Methods:
        start_service(cls) -> None:
            Start the Docker service.

        stop_service(cls) -> None:
            Stop the running Docker service.

        kill_service(cls) -> None:
            Kills the running Docker service.

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

    def __init__(self, custom_config_path: Optional[str] = None) -> None:
        """Initialize DockerCLIWrapper class."""
        if custom_config_path:
            self._load_custom_config(custom_config_path)

    @classmethod
    def run_docker_command(cls, command: str) -> None:
        """Run a Docker CLI command.

        Args:
            command: The Docker CLI command to run.
        """
        try:
            output = subprocess.check_output(
                args=command,
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
    def start_service(cls) -> None:
        """Start the Docker service."""
        cls.run_docker_command("docker-compose -f - up -d")

    @classmethod
    def stop_service(cls) -> None:
        """Stop the running Docker service."""
        cls.run_docker_command("docker-compose -f - stop")

    @classmethod
    def kill_service(cls) -> None:
        """Kill the running Docker service."""
        cls.run_docker_command("docker-compose -f - down")

    @classmethod
    def restart_service(cls, hard: bool) -> None:
        """Restart the running Docker service."""
        if hard:
            cls.run_docker_command("docker-compose -f - down")
            cls.run_docker_command("docker-compose -f - up -d")
        else:
            cls.run_docker_command("docker-compose -f - restart")

    @classmethod
    def _load_custom_config(cls, custom_config_path: str) -> None:
        """Load a custom Docker Compose config file.

        Args:
            custom_config_path: Path to the custom Docker Compose config file.
        """
        try:
            with open(
                file=custom_config_path, mode="r", encoding="utf-8"
            ) as file:
                cls._docker_compose_config = file.read()
        except FileNotFoundError:
            print(
                f"FileNotFoundError: Custom config file `{custom_config_path}`"
                f" not found."
            )
            sys.exit(1)


@click.group()
@click.option(
    "-c",
    "--config",
    help="Path to the custom Docker Compose config file.",
)
@click.pass_context
def service(ctx: Context, config: Optional[str] = None) -> None:
    """Manage Aineko docker services (Kafka and Zookeeper containers)."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@service.command()
@click.pass_context
def start(ctx: Context) -> None:
    """Start Aineko docker services."""
    DockerCLIWrapper(ctx.obj["config"]).start_service()


@service.command()
@click.pass_context
def stop(ctx: Context) -> None:
    """Stop Aineko docker services."""
    DockerCLIWrapper(ctx.obj["config"]).stop_service()


@service.command()
@click.pass_context
def down(ctx: Context) -> None:
    """Kill Aineko docker services."""
    DockerCLIWrapper(ctx.obj["config"]).kill_service()


@service.command()
@click.option(
    "-H",
    "--hard",
    is_flag=True,
    help=(
        "Forces full restart Aineko docker services."
        "Clears data from Kafka cache."
    ),
)
@click.pass_context
def restart(ctx: Context, hard: bool = True) -> None:
    """Restart Aineko docker services."""
    DockerCLIWrapper(ctx.obj["config"]).restart_service(hard=hard)
