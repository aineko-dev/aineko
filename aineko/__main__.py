# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Aineko command line interface."""
import click

from aineko import __version__
from aineko.cli.create_pipeline import create
from aineko.cli.docker_cli_wrapper import service
from aineko.cli.kafka_cli_wrapper import stream
from aineko.cli.run import run
from aineko.cli.visualize import visualize


@click.group()
def aineko() -> None:
    """Aineko CLI."""
    pass


@aineko.command()
def version() -> None:
    """Prints the version of Aineko."""
    click.echo(__version__)


aineko.add_command(create)
aineko.add_command(run)
aineko.add_command(service)
aineko.add_command(stream)
aineko.add_command(visualize)

if __name__ == "__main__":
    aineko(obj={})
