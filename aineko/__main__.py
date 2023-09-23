"""Aineko command line interface."""
import argparse

from aineko import __version__
from aineko.cli.docker_cli_wrapper import DockerCLIWrapper
from aineko.cli.kafka_cli_wrapper import KafkaCLIWrapper
from aineko.cli.run import main as run_main
from aineko.cli.visualize import render_mermaid_graph


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

    # `aineko run *`
    run_parser = subparsers.add_parser("run", help="Run a pipeline")
    run_parser.add_argument(
        "-c",
        "--config_file",
        help="Path to the config file containing pipeline config.",
        type=str,
        required=True,
    )
    run_parser.add_argument(
        "-p",
        "--pipeline_name",
        help="Name of the pipeline",
        type=str,
        default=None,
    )

    run_parser.set_defaults(
        func=lambda args: run_main(
            pipeline_config_file=args.config_file,
            pipeline=args.pipeline_name,
        )
    )

    # `aineko service *`
    service_parser = subparsers.add_parser("service")
    service_subparsers = service_parser.add_subparsers()

    start_service_parser = service_subparsers.add_parser("start")
    start_service_parser.add_argument(
        "-f",
        "--file",
        help=(
            "Specify a relative path to a docker-compose file (optional) for"
            " the 'start' command"
        ),
    )
    start_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.start_service(args.file)
    )

    stop_service_parser = service_subparsers.add_parser("stop")
    stop_service_parser.add_argument(
        "-f",
        "--file",
        help=(
            "Specify a relative path to a docker-compose file (optional) for"
            " the 'stop' command"
        ),
    )
    stop_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.stop_service(args.file)
    )

    restart_service_parser = service_subparsers.add_parser("restart")
    restart_service_parser.add_argument(
        "-f",
        "--file",
        help=(
            "Specify a relative path to a docker-compose file (optional) for"
            " the 'restart' command"
        ),
    )
    restart_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.restart_service(args.file)
    )

    # `aineko stream *`
    stream_parser = subparsers.add_parser("stream")

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

    # `aineko visualize *`
    visualize_parser = subparsers.add_parser(
        "visualize", help="Visualize Aineko pipelines as a Mermaid graph."
    )
    visualize_parser.add_argument(
        "config_path",
        type=str,
        help="Path to pipeline yaml file.",
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    _cli()
