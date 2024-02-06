# Introduction to plugins

Aineko comes with a set of optional plugins that can be added to your pipeline. Currently these plugins are extra nodes with a focus on popular use-cases and best-practice patterns.
To use one of these nodes, simply add it to your dependencies and reference in it in the pipeline configuration.

## Adding Dependencies

To install the dependencies of a plugin, modify your `pyproject.toml` file by adding the `extras` key to the `aineko` package.

:   
    ```yaml title="pyproject.toml" hl_lines="3"
    [tool.poetry.dependencies]
    python = ">=3.8,<3.12"
    aineko = {version = "^0.3.0", extras=["fastapi-server"]}
    ```

Once added, install the required dependencies using 

:   
    ```bash
    $ poetry lock
    $ poetry install
    ```

## Reference in Pipeline Configuration

To use such a node, simply reference the class in your pipeline configuration.

:   
    ```yaml title="pipeline.yml"
    nodes:
      fastapi:
        class: aineko_plugins.nodes.fastapi_server.FastAPI
        inputs:
          - test_sequence
        node_params:
          app: my_awesome_pipeline.fastapi:app
          port: 8000
    ```

Refer to the in-depth pages on each extra node for more detail on how to use them.