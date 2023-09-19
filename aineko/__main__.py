"""Aineko command line interface."""
import argparse

from aineko import __version__
from aineko.cli.run import main as run_main
from aineko.cli.visualize import (
    build_mermaid_from_yaml,
    render_graph_in_browser,
)


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

    subparsers = parser.add_subparsers(dest="command")

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
        nargs="?",
    )

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

    args = parser.parse_args()

    if args.command == "run":
        run_main(
            pipeline_config_file=args.config_file,
            pipeline=args.pipeline_name,
        )
    elif args.command == "visualize":
        graph = build_mermaid_from_yaml(
            config_path=args.config_path,
            direction=args.direction,
            legend=args.legend,
        )
        if args.browser:
            render_graph_in_browser(mermaid_graph=graph)
        else:
            print(graph)

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
