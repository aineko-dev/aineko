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

Aineko comes with a light weight helper function as follows:

::: aineko.extras.fastapi.health.read_health

## Authentication Considerations

By default, the Aineko health endpoint does not contain authentication. 

One method to add authentication is to use security middleware at the app level for FastAPI. This will handle adding authentication to the health endpoint without having to add custom dependencies.