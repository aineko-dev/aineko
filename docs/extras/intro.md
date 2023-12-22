# Introduction to Extras

Extra nodes are nodes that come shipped with the `aineko` package. They cover popular use-cases and follow best-practice patterns to accelerate your speed of development.

To use one of these nodes, simply add it to your dependencies and reference in it in the pipeline configuration.

## Adding Dependencies

To install the dependencies of an extra node submodule, modify your `pyproject.toml` file by adding the `extras` key to the `aineko` package.

:   
    ```yaml title="pyproject.toml" hl_lines="3"
    [tool.poetry.dependencies]
    python = ">=3.10,<3.11"
    aineko = {version = "^0.2.7", extras=["fastapi"]}
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
        class: aineko.extras.FastAPI
        inputs:
          - test_sequence
        node_params:
          app: my_awesome_pipeline.fastapi:app
          port: 8000
    ```

Refer to the in-depth pages on each extra node for more detail on how to use them.