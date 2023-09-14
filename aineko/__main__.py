"""Aineko command line interface."""
import argparse

from aineko import __version__

from aineko.cli.DockerCLIWrapper import DockerCLIWrapper


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

    service_parser = subparsers.add_parser("service")
    service_subparsers = service_parser.add_subparsers()

    start_service_parser = service_subparsers.add_parser("start")
    start_service_parser.add_argument(
    "-f", "--file", help="Specify a relative path to a docker-compose file (optional) for the 'start' command")
    start_service_parser.set_defaults(func=lambda args: DockerCLIWrapper.start_service(args.file))

    stop_service_parser = service_subparsers.add_parser("stop")
    stop_service_parser.add_argument(
    "-f", "--file", help="Specify a relative path to a docker-compose file (optional) for the 'stop' command")
    stop_service_parser.set_defaults(func=lambda args: DockerCLIWrapper.stop_service(args.file))

    restart_service_parser = service_subparsers.add_parser("restart")
    restart_service_parser.add_argument(
    "-f", "--file", help="Specify a relative path to a docker-compose file (optional) for the 'restart' command")
    restart_service_parser.set_defaults(func=lambda args: DockerCLIWrapper.restart_service(args.file))

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    _cli()
