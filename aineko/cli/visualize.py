# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Visualize Aineko pipelines as a Mermaid graph."""
import os
import webbrowser

import click
import yaml


@click.command()
@click.argument("config_path")
@click.option(
    "-d",
    "--direction",
    type=click.Choice(["TD", "LR"]),
    default="LR",
    help=(
        "Direction of the graph. Either LR (left to right) or" " TD (top down)."
    ),
)
@click.option(
    "-l",
    "--legend",
    is_flag=True,
    help="Include a legend in the graph.",
)
@click.option(
    "-b",
    "--browser",
    is_flag=True,
    help="Render graph in browser. Prints graph to stdout otherwise.",
)
def visualize(
    config_path: str,
    direction: str = "LR",
    legend: bool = False,
    browser: bool = False,
) -> None:
    """Builds mermaid graph from an Aineko pipeline config.\f

    Args:
        config_path: file path to pipeline yaml file
        direction: direction of the graph.
        legend: include a legend in the graph.
        browser: Whether to render graph in browser. Prints graph to stdout
            otherwise.
    """
    graph = build_mermaid_from_yaml(
        config_path=config_path, direction=direction, legend=legend
    )
    if browser:
        render_graph_in_browser(graph)

    else:
        print(graph)


def build_mermaid_from_yaml(
    config_path: str, direction: str = "LR", legend: bool = False
) -> str:
    """Builds mermaid graph from an Aineko pipeline config.

    Args:
        config_path: file path to pipeline yaml file
        direction: direction of the graph.
        legend: include a legend in the graph.

    Returns:
        A mermaid graph as a string.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        text = f.read()
    root = yaml.safe_load(text)
    pipeline_name = next(iter(root))
    nodes = root[pipeline_name]["nodes"]

    transitions = []
    for node_name, node_subscriptions in nodes.items():
        if "inputs" in node_subscriptions:
            for input_dataset in node_subscriptions["inputs"]:
                transitions.append({"input": input_dataset, "node": node_name})
        if "outputs" in node_subscriptions:
            for output_dataset in node_subscriptions["outputs"]:
                transitions.append(
                    {"node": node_name, "output": output_dataset}
                )
        if (
            "inputs" not in node_subscriptions.keys()
            and "outputs" not in node_subscriptions.keys()
        ):
            transitions.append({"node": node_name})

    mermaid_transitions = []

    for transition in transitions:
        if (
            not "input" in transition.keys()
            and not "output" in transition.keys()
        ):
            mermaid_transitions.append(
                f"N_{transition['node']}(({transition['node']})):::nodeClass"
            )
        else:
            if "input" in transition.keys():
                src_node = (
                    f"T_{transition['input']}[{transition['input']}]"
                    ":::datasetClass"
                )
                tgt_node = f"N_{transition['node']}(({transition['node']})):::nodeClass"  # pylint: disable=line-too-long
            elif "output" in transition.keys():
                src_node = f"N_{transition['node']}(({transition['node']})):::nodeClass"  # pylint: disable=line-too-long
                tgt_node = (
                    f"T_{transition['output']}[{transition['output']}]"
                    ":::datasetClass"
                )

            mermaid_transitions.append(f"{src_node} -->  {tgt_node}")

    header = f"flowchart {direction}\nclassDef datasetClass "
    header += "fill:#87CEEB\nclassDef nodeClass fill:#eba487"

    if legend:
        footer = (
            "subgraph Legend\nnode((Node)):::nodeClass\ndataset[Dataset]"
            ":::datasetClass\nend\n"
        )
    else:
        footer = ""

    mermaid = "\n".join([header, *mermaid_transitions, footer])
    return mermaid


def render_graph_in_browser(mermaid_graph: str) -> None:
    """Renders a mermaid graph in the default browser.

    Note:
        requires internet connection to load mermaid js.

    Args:
        mermaid_graph: the mermaid graph to render.
    """
    mermaid_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <body>
        <pre class="mermaid">
        {mermaid_graph}
        </pre>
        <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        </script>
    </body>
    </html>
    """
    cwd = os.getcwd()
    with open(f"{cwd}/mermaid.html", "w", encoding="utf-8") as f:
        f.write(mermaid_html)
    webbrowser.open(f"file://{cwd}/mermaid.html")
