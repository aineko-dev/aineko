# FastAPI Node

The FastAPI extra node can be used by adding the following to `pyproject.toml`

:   
    ```yaml title="pyproject.toml" hl_lines="2"
    [tool.poetry.dependencies]
    aineko = {version = "^0.2.7", extras=["fastapi"]}
    ```

## API Reference

::: aineko.extras.fastapi.main.FastAPI

# Health Check Endpoint

A common use case with an API server is to check its operational health status. For Aineko specifically, it is useful to know if the pipeline and API node are operational as well. Aineko comes with a light weight helper function as follows:

::: aineko.extras.fastapi.health.read_health

## Authentication Considerations

By default, the `/health` endpoint does not contain authentication. 

One method to add authentication is to use security middleware at the app level for FastAPI. This will handle adding authentication to the health endpoint without having to add custom dependencies.

For more information about security with FastAPI, check out the documentation [here](https://fastapi.tiangolo.com/advanced/security/).
