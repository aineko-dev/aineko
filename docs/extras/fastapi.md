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

A health check endpoint can be imported and added to the FastAPI app as follows:

```python title="" hl_lines="2 6"
from fastapi import FastAPI
from aineko.extras.fastapi import health_router

app = FastAPI()

app.include_router(health_router)
```

The health check endpoint is available via a GET request to the `/health` route and returns a 200 response if the server is active.

For example, if the FastAPI app is running locally on `http://localhost:8000`, the health check endpoint can be accessed via a GET request query to `http://localhost:8000/health`.
