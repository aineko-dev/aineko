# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Health endpoint for FastAPI server."""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health", status_code=200)
async def read_health() -> dict:
    """Return the health status of the Aineko FastAPI server.

    Health router can be imported by an Aineko FastAPI server and added
    to the app as a router.

    The health check endpoint is available via a GET request to the `/health`
    route and returns a 200 response if the server is active.

    For example, if the FastAPI app is running locally on
    `http://localhost:8000`, the health check endpoint can be accessed via
    a GET request query to `http://localhost:8000/health`.

    Example usage in FastAPI app:
        ```python hl_lines="2 5"
        from fastapi import FastAPI
        from aineko.extras.fastapi import health_router

        app = FastAPI()
        app.include_router(health_router)
        ```
    """
    return {"status": "healthy"}
