"""Aineko command line interface."""
import argparse

from aineko.cli.provision import main as provision_main
from aineko.cli.run import main as run_main
from aineko.cli.validate import main as validate_main
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

    subparsers = parser.add_subparsers(dest="command")

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
    run_parser.add_argument(
        "-t", "--test", help="Only run test pipelines", action="store_true"
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

    provision_parser = subparsers.add_parser(
        "provision", help="Provision a project."
    )

    provision_parser.add_argument(
        "-e",
        "--env",
        help="Environment to provision",
        default="develop",
        nargs="?",
    )

    provision_parser.add_argument(
        "-c",
        "--conf_source",
        help="Path to the directory containing the configuration files.",
        type=str,
        default=None,
        nargs="?",
    )
    provision_parser.add_argument(
        "-d",
        "--destroy",
        help="Destroy pipeline resources.",
        action="store_true",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate Aineko pipeline datasets to ensure "
        "consistency between catalog and pipeline yaml files.",
    )

    validate_parser.add_argument(
        "-c",
        "--conf_source",
        help="Path to the directory containing the configuration files.",
        type=str,
        default=None,
        nargs="?",
    )
    validate_parser.add_argument(
        "-p",
        "--project_names",
        nargs="+",
        required=True,
        help="Project name(s) to load config for.",
    )

    validate_parser.add_argument(
        "-d",
        "--project_dir",
        type=str,
        help="Path to project directory containing python code.",
    )

    validate_parser.add_argument(
        "-f",
        "--fix_catalog",
        action="store_true",
        help="Flag to fix catalog yaml file by adding datasets",
    )

    args = parser.parse_args()

    if args.command == "run":
        run_main(
            project=args.project_name,
            pipeline=args.pipeline_name,
            conf_source=args.conf_source,
            test_mode=args.test,
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

    elif args.command == "provision":
        provision_main(
            env=args.env,
            conf_source=args.conf_source,
            destroy=args.destroy,
        )

    elif args.command == "validate":
        validate_main(
            project_names=args.project_names,
            conf_source=args.conf_source,
            project_dir=args.project_dir,
            fix_catalog=args.fix_catalog,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
