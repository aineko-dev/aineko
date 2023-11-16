# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""
Node for creating a FastAPI app with a gunicorn server.

Use it in your Aineko pipeline config as follows:

```
pipeline:
  nodes:
    fastapi:
      class: aineko.nodes.fastapi
      node_params:
        app: my_project.app
        port: 8000
```

See https://fastapi.tiangolo.com/ for documentation on how to create a FastAPI app.
"""

from typing import Optional

import uvicorn

from aineko.core import AbstractNode


class FastAPI(AbstractNode):
    """Node that runs the API server.

    Uvicorn is the HTTP server that runs the FastAPI app.
    The endpoints and logic for the app is contained in fieldcircus/api.
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Initialize node state. Set env variables for Fast API app."""
        pass

    def _execute(self, params: Optional[dict] = None) -> None:
        """Start the API server."""
        if params is None:
            raise ValueError("Missing params for FastAPI node.")

        config = uvicorn.Config(
            app=params.get("app"),  # type: ignore
            port=params.get("port", 8000),
            log_level="info",
            host="0.0.0.0",
        )
        server = uvicorn.Server(config)
        server.run()
