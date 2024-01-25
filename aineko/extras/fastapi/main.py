# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for running a FastAPI server.

This module contains the Consumers and Producers class that give
access to the node's consumers and producers from within the FastAPI
app. It also contains the FastAPI node class that runs the uvicorn
server.

We recommend no more than 1 FastAPI node per pipeline since the Consumer
and Producer objects are namespaced at the pipeline level. If you must
have multiple FastAPI nodes, we recommend using different datasets to avoid
namespace collisions.
"""

from typing import Optional, Union

import uvicorn

from aineko import AbstractNode, DatasetConsumer, DatasetProducer


class Consumers(dict):
    """Class to contain consumers."""

    def __setitem__(
        self, key: Union[str, int, tuple], value: DatasetConsumer
    ) -> None:
        """Checks that item is of type DatasetConsumer before setting.

        Args:
            key: Name of the dataset
            value: DatasetConsumer object to be stored

        Raises:
            ValueError: If value is not of type DatasetConsumer
        """
        if not isinstance(value, DatasetConsumer):
            raise ValueError(
                f"Value must be of type DatasetConsumer, not {type(value)}"
            )
        super().__setitem__(key, value)


class Producers(dict):
    """Class to contain producers."""

    def __setitem__(
        self, key: Union[str, int, tuple], value: DatasetProducer
    ) -> None:
        """Checks that item is of type DatasetProducer before setting.

        Args:
            key: Name of the dataset
            value: DatasetProducer object to be stored

        Raises:
            ValueError: If value is not of type DatasetProducer
        """
        if not isinstance(value, DatasetProducer):
            raise ValueError(
                f"Value must be of type DatasetProducer, not {type(value)}"
            )
        super().__setitem__(key, value)


consumers = Consumers()
producers = Producers()


class FastAPI(AbstractNode):
    """Node for creating a FastAPI app with a gunicorn server.

    `node_params` should contain the following keys:

        app: path to FastAPI app
        port (optional): port to run the server on. Defaults to 8000.
        log_level (optional): log level to log messages from the uvicorn server.
            Defaults to "info".

    To access the consumers and producers from your FastAPI app, import the
    `consumers` and `producers` variables from `aineko.extras.fastapi`. Use
    them as you would use `self.consumers` and `self.producers` in a regular
    node.

    We recommend no more than 1 FastAPI node per pipeline since the Consumer
    and Producer objects are namespaced at the pipeline level.

    Example usage in pipeline.yml:
    ```yaml title="pipeline.yml"
    pipeline:
      nodes:
        fastapi:
          class: aineko.extras.FastAPI
          inputs:
            - test_sequence
          node_params:
            app: my_awesome_pipeline.fastapi:app
            port: 8000
    ```
    where the app points to a FastAPI app. See
    [FastAPI documentation](https://fastapi.tiangolo.com/){:target="_blank"}
    on how to create a FastAPI app.

    Example usage in FastAPI app:
    ```python title="fastapi.py"
    from aineko.extras.fastapi import consumers, producers

    @app.get("/query")
    async def query():
        msg = consumers["test_sequence"].next()
        return msg
    ```
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Initialize node state. Set env variables for Fast API app."""
        for key, value in self.consumers.items():
            consumers[key] = value
        for key, value in self.producers.items():
            producers[key] = value

    def _execute(self, params: dict) -> None:
        """Start the API server."""
        config = uvicorn.Config(
            app=params.get("app"),  # type: ignore
            port=params.get("port", 8000),
            log_level=params.get("log_level", "info"),
            host="0.0.0.0",
        )
        server = uvicorn.Server(config)
        server.run()
