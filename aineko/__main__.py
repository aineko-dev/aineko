"""Aineko command line interface."""
import argparse

from aineko import __version__

from aineko.cli.DockerCLIWrapper import DockerCLIWrapper
from aineko.cli.KafkaCLIWrapper import KafkaCLIWrapper
from aineko.cli.run import main as run_main


def _cli() -> None:
    """Command line interface for Aineko."""
    parser = argparse.ArgumentParser(
        prog="aineko",
        description="Aineko is a framework for building data intensive "
        "applications.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers()

    # `aineko run *`
    service_parser = subparsers.add_parser("run", help="Runs a pipeline")
    run_parser = subparsers.add_parser("run", help="Run a pipeline")
    run_parser.add_argument(
        "-p",
        "--project_name",
        help="Name of the project",
        type=str,
        required=True,
    )
    run_parser.add_argument(
        "-pi",
        "--pipeline_name",
        help="Name of the pipeline",
        type=str,
        required=True,
    )
    run_parser.add_argument(
        "-c",
        "--conf_source",
        help="Path to the directory containing the configuration files.",
        type=str,
        default=None,
        nargs="?",
    )

    run_parser.set_defaults(
        func=lambda args: run_main(
            project=args.project_name,
            pipeline=args.pipeline_name,
            conf_source=args.conf_source,
        )
    )

    # `aineko service *`
    service_parser = subparsers.add_parser("service")
    service_subparsers = service_parser.add_subparsers()

    start_service_parser = service_subparsers.add_parser("start")
    start_service_parser.add_argument(
        "-f",
        "--file",
        help="Specify a relative path to a docker-compose file (optional) for the 'start' command",
    )
    start_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.start_service(args.file)
    )

    stop_service_parser = service_subparsers.add_parser("stop")
    stop_service_parser.add_argument(
        "-f",
        "--file",
        help="Specify a relative path to a docker-compose file (optional) for the 'stop' command",
    )
    stop_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.stop_service(args.file)
    )

    restart_service_parser = service_subparsers.add_parser("restart")
    restart_service_parser.add_argument(
        "-f",
        "--file",
        help="Specify a relative path to a docker-compose file (optional) for the 'restart' command",
    )
    restart_service_parser.set_defaults(
        func=lambda args: DockerCLIWrapper.restart_service(args.file)
    )

    # `aineko dataset *`
    dataset_parser = subparsers.add_parser("dataset")
    dataset_subparser = dataset_parser.add_subparsers()

    view_dataset_parser = dataset_subparser.add_parser("view", help="View all previous messages and new ones for the dataset")
    view_dataset_parser.add_argument(
        "-d",
        "--dataset",
        help= "Name of dataset",
        required=True
    )
    view_dataset_parser.set_defaults(func=lambda args: KafkaCLIWrapper.view_dataset(args.dataset))

    stream_dataset_parser = dataset_subparser.add_parser("stream", help="Stream new messages for the dataset")
    stream_dataset_parser.add_argument(
        "-d",
        "--dataset",
        help="Name of dataset",
        required=True,
    )
    stream_dataset_parser.set_defaults(func=lambda args: KafkaCLIWrapper.stream_dataset(args.dataset))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    _cli()
