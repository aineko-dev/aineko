# FastAPI Node

## Installation

The FastAPI plugin can be installed using poetry with the following command `poetry add aineko[fastapi-server]` or by adding the following to `pyproject.toml` and running `poetry install`:

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.3.2", extras=["fastapi-server"]}
    ```

## API Reference

::: aineko_plugins.nodes.fastapi_server.FastAPI

# Health Check Endpoint

A common use case with an API server is to check its operational health status. For Aineko specifically, it is useful to know if the pipeline and API node are operational as well. Aineko comes with a light weight helper function as follows:

::: aineko_plugins.nodes.fastapi_server.health.read_health

## Authentication Considerations

By default, the `/health` endpoint does not contain authentication. 

One method to add authentication is to use security middleware at the app level for FastAPI. This will handle adding authentication to the health endpoint without having to add custom dependencies.

For more information about security with FastAPI, check out the documentation [here](https://fastapi.tiangolo.com/advanced/security/).
