# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Health endpoint for FastAPI server.

Health router can be imported by any FastAPI server to
add a health GET endpoint at /health.

Example:
    ```from fastapi import FastAPI
    from aineko.extras.fastapi import health_router

    app = FastAPI()
    app.include_router(health_router)```
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def read_health():
    """Return the health status of the FastAPI server."""
    return {"status": "healthy"}
