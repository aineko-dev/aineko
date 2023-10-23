# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Aineko command line interface."""
import argparse

from aineko import __version__
from aineko.cli.create_pipeline import create_pipeline_directory
from aineko.cli.docker_cli_wrapper import DockerCLIWrapper
from aineko.cli.kafka_cli_wrapper import KafkaCLIWrapper
from aineko.cli.run import main as run_main
from aineko.cli.visualize import render_mermaid_graph


def _create_parser(subparser: argparse._SubParsersAction) -> None:
    """Subparser for the `aineko create` command.

    Args:
        subparser: Subparser for the `aineko` command.
    """
    create_parser = subparser.add_parser(
        "create",
        help="Create a directory containing pipeline config and \
            code from a template to get started",
    )
    create_parser.add_argument(
        "-d",
        "--deployment-config",
        action="store_true",
        help="Include deploy.yml that facilitates deployment of pipelines",
    )
    create_parser.set_defaults(
        func=lambda args: create_pipeline_directory(args.deployment_config)
    )


def _run_parser(subparser: argparse._SubParsersAction) -> None:
    """Subparser for the `aineko run` command.

    Args:
        subparser: Subparser for the `aineko` command.
    """
    run_parser = subparser.add_parser("run", help="Run a pipeline")
    run_parser.add_argument(
        "config_path",
        help="Path to the config file containing the pipeline config.",
        type=str,
    )
    run_parser.add_argument(
        "-p", "--pipeline", help="Name of the pipeline to run (optional)."
    )
    run_parser.set_defaults(
        func=lambda args: run_main(
            pipeline_config_file=args.config_path, pipeline_name=args.pipeline
        )
    )


def _service_parser(parser: argparse._SubParsersAction) -> None:
    """Subparser for the `aineko service` command."""
    service_parser = parser.add_parser(
        "service", help="Manage Aineko related services"
    )
    service_subparsers = service_parser.add_subparsers()

    start_service_parser = service_subparsers.add_parser(
        "start", help="Start Aineko related services"
    )

    start_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.start_service()
    )

    stop_service_parser = service_subparsers.add_parser(
        "stop", help="Stop Aineko related services"
    )

    stop_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.stop_service()
    )

    restart_service_parser = service_subparsers.add_parser(
        "restart", help="Restart Aineko related services"
    )

    restart_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.restart_service()
    )


def _stream_parser(subparser: argparse._SubParsersAction) -> None:
    """Subparser for the `aineko stream` command.

    Args:
        subparser: Subparser for the `aineko` command.
    """
    stream_parser = subparser.add_parser(
        "stream", help="Stream messages from a dataset"
    )

    stream_parser.add_argument(
        "-d", "--dataset", help="Name of dataset", required=True
    )
    stream_parser.add_argument(
        "--from-start",
        help="If we should stream messages from the start or not",
        action="store_true",
    )

    # consume from beginning
    stream_parser.set_defaults(
        func=lambda args: KafkaCLIWrapper.consume_kafka_topic(
            args.dataset, from_beginning=args.from_start
        )
    )


def _visualize_parser(subparser: argparse._SubParsersAction) -> None:
    """Subparser for the `aineko visualize` command.

    Args:
        subparser: Subparser for the `aineko` command.
    """
    visualize_parser = subparser.add_parser(
        "visualize", help="Visualize Aineko pipelines as a Mermaid graph."
    )
    visualize_parser.add_argument(
        "config_path",
        type=str,
        help="Path to the config file containing the pipeline config.",
    )
    visualize_parser.add_argument(
        "-d",
        "--direction",
        type=str,
        default="LR",
        help=(
            "Direction of the graph. Either LR (left to right) or"
            " TD (top down)."
        ),
        choices=["TD", "LR"],
    )
    visualize_parser.add_argument(
        "-l",
        "--legend",
        action="store_true",
        help="Include a legend in the graph.",
    )
    visualize_parser.add_argument(
        "-b",
        "--browser",
        action="store_true",
        help="Open the graph in the default browser.",
    )
    visualize_parser.set_defaults(
        func=lambda args: render_mermaid_graph(
            config_path=args.config_path,
            direction=args.direction,
            legend=args.legend,
            render_in_browser=args.browser,
        )
    )


def _cli() -> None:
    """Command line interface for Aineko."""
    parser = argparse.ArgumentParser(
        prog="aineko",
        description=(
            "Aineko is a framework for building data intensive applications."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers()
    _create_parser(subparsers)
    _run_parser(subparsers)
    _service_parser(subparsers)
    _stream_parser(subparsers)
    _visualize_parser(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
