# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Aineko command line interface."""
import click

from aineko import __version__
from aineko.cli.create_pipeline import create
from aineko.cli.docker_cli_wrapper import service
from aineko.cli.dream import dream
from aineko.cli.kafka_cli_wrapper import stream
from aineko.cli.run import run
from aineko.cli.visualize import visualize


@click.group("aineko", context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
def cli() -> None:
    """Aineko CLI."""
    pass


cli.add_command(create)
cli.add_command(run)
cli.add_command(service)
cli.add_command(stream)
cli.add_command(visualize)
cli.add_command(dream)

if __name__ == "__main__":
    cli(obj={})
