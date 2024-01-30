# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a WebSocket server."""

import json
import time
from typing import Any, Dict, List, Optional

import websocket
from pydantic import BaseModel, field_validator

from aineko import AbstractNode


class ParamsWebSocketClient(BaseModel):
    """Parameters for the WebSocketClient node.

    Attributes:
        max_retries: The maximum number of times to retry connecting to the
            WebSocket. Defaults to -1 (retry forever).
        retry_sleep: The number of seconds to wait between retries. Defaults
            to 5.
        url: The WebSocket URL to connect to.
        header: A dictionary of headers to send to the WebSocket. Defaults to
            None.
        init_messages: A list of messages to send to the WebSocket upon
            connection. Defaults to [].
        metadata: A dictionary of metadata to attach to outgoing messages.
            Defaults to None.

    Raises:
        ValueError: If the url is not a valid WebSocket URL.
    """

    max_retries: int = -1
    retry_sleep: float = 5
    url: str
    header: Optional[Dict[str, str]] = None
    init_messages: List[Any] = []
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("url")
    @classmethod
    def supported_url(cls, url: str) -> str:
        """Validates that the url is a valid WebSocket URL."""
        if not (url.startswith("wss://") or url.startswith("ws://")):
            raise ValueError(
                "Invalid url provided to WebSocket params. "
                'Expected url to start with "wss://" or "ws://". '
                f"Provided url was: {url}"
            )
        return url


class WebSocketClient(AbstractNode):
    """Node for ingesting data from a WebSocket.

    This node is a wrapper around the
    [websocket-client](
        https://websocket-client.readthedocs.io/en/latest/index.html
        ){:target="_blank"} library.

    Example usage in pipeline.yml:
    ```yaml title="pipeline.yml"
    pipeline:
      nodes:
        WebSocketClient:
          class: aineko.extras.WebSocketClient
          outputs:
            - test_websocket
          node_params:
            url: "wss://example.com"
            header:
              auth: "Bearer {$SECRET_NAME}"
            init_messages:
                - {"Greeting": "Hello, world!"}
    ```

    Note that the `outputs` field is required and must contain exactly one
    output dataset. The output dataset will contain the data returned by the
    WebSocket.

    Secrets can be injected (from environment) into the `url`, `header`, and
    `init_messages` fields by passing a string with the following format:
    `{$SECRET_NAME}`. For example, if you have a secret named `SECRET_NAME`
    with value `SECRET_VALUE`, you can inject it into the url field by passing
    `wss://example.com?secret={$SECRET_NAME}` as the url. The connector will
    then replace `{$SECRET_NAME}` with `SECRET_VALUE` before connecting to the
    WebSocket.

    By default, if the WebSocket connection is closed or an error occurs, the
    connector will retry connecting to the WebSocket indefinitely every 5
    seconds. No headers or initialization messages are sent to the WebSocket.
    """

    retry_count = 0

    def _pre_loop_hook(self, params: Optional[Dict] = None) -> None:
        """Initialize the WebSocket connection.

        Raises:
            ValueError: If the params are invalid.
        """
        try:
            if params is not None:
                self.ws_params = ParamsWebSocketClient(**params)
            else:
                raise ValueError(
                    "No params provided to WebSocket connector. "
                    "Node requires at least a url param."
                )
        except Exception as err:  # pylint: disable=broad-except
            # Cast pydantic validation error to ValueError
            # so that it can be properly caught by the node
            # Note: this is required because pydantic errors
            # are not picklable
            raise ValueError(
                "Failed to cast params to ParamsWebSocketClient type. "
                f"The following error occurred: {err}"
            ) from err

        # Ensure only one output dataset is provided
        output_datasets = [
            dataset for dataset in self.producers.keys() if dataset != "logging"
        ]
        if len(output_datasets) > 1:
            raise ValueError(
                "Only one output dataset is allowed for the "
                "WebSocketClient connector. "
                f"{len(output_datasets)} datasets given."
            )
        self.output_dataset = output_datasets[0]

        # Create the websocket subscription
        self.ws = websocket.WebSocket()
        self.create_subscription()

    def _execute(self, params: Optional[Dict] = None) -> None:
        """Polls and gets data from the WebSocket.

        Raises:
            ValueError: If the retry count exceeds the max retries.
        """
        try:
            # Poll the websocket
            raw_message = self.ws.recv()
        except Exception as err:  # pylint: disable=broad-except
            # If the connection is closed, reconnect
            self.log(
                "Websocket connection closed. "
                f"Reconnecting in {self.ws_params.retry_sleep} "
                f"seconds... The following error occurred: {err}",
                level="error",
            )
            time.sleep(self.ws_params.retry_sleep)
            self.create_subscription()
            return

        try:
            # Parse the message and emit to producers
            message = json.loads(raw_message)
            if self.ws_params.metadata is not None:
                message = {
                    "metadata": self.ws_params.metadata,
                    "data": message,
                }
            self.producers[self.output_dataset].produce(message)
            self.retry_count = 0
        except json.decoder.JSONDecodeError as err:
            if self.retry_count < self.ws_params.max_retries:
                self.retry_count += 1
                self.log(
                    f"Failed to parse message: {raw_message!r}. "
                    f"The following error occurred: {err} "
                    f"Reconnecting in {self.ws_params.retry_sleep} "
                    "seconds...",
                    level="error",
                )
                time.sleep(self.ws_params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries "
                    f"({self.ws_params.max_retries}). "
                    f"Failed to parse message: {raw_message!r}. "
                    f"The following error occurred: {err}"
                ) from err

    def create_subscription(self) -> None:
        """Creates a subscription on the websocket.

        Raises:
            Exception: If the retry count exceeds the max retries.
        """
        try:
            self.log(f"Creating subscription to {self.ws_params.url}...")
            self.ws.connect(
                url=self.ws_params.url, header=self.ws_params.header
            )  # type: ignore

            if self.ws_params.init_messages:
                # Send initialization messages
                for init_msg in self.ws_params.init_messages:
                    self.ws.send(json.dumps(init_msg))
                    message = self.ws.recv()
                    self.log(
                        "Sent initialization message to "
                        f"{self.ws_params.url}. "
                        f"Acknowledged initialization message: {message!r}"
                    )

            ack_message = self.ws.recv()
            self.log(
                f"Subscription to {self.ws_params.url} created. "
                f"Acknowledged subscription message: {ack_message!r}"
            )

            self.retry_count = 0
        except Exception as err:  # pylint: disable=broad-except
            if self.retry_count < self.ws_params.max_retries:
                self.log(
                    "Encountered error when attempting to connect to "
                    f"{self.ws_params.url}. Will retry in "
                    f"{self.ws_params.retry_sleep} seconds"
                )
                self.retry_count += 1
                time.sleep(self.ws_params.retry_sleep)
                self.create_subscription()
            else:
                raise Exception(  # pylint: disable=broad-exception-raised
                    "Retry count exceeded max retries. "
                    "Failed to create subscription to "
                    f"{self.ws_params.url}. "
                    f"The following error occurred: {err}"
                ) from err
