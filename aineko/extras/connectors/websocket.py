# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a WebSocket."""

import json
import time
from typing import Any, Dict, List, Optional

import websocket
from pydantic import BaseModel, field_validator

from aineko import AbstractNode
from aineko.extras.connectors.secrets import inject_secrets


class ParamsWebSocket(BaseModel):
    """Connector params for WebSocket model."""

    max_retries: int = 30
    retry_sleep: float = 5
    url: str
    header: Optional[Dict[str, str]] = None
    init_messages: List[Any] = []
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("url")
    def supported_url(cls, u: str) -> str:  # pylint: disable=no-self-argument
        """Validates that the url is a valid WebSocket URL."""
        if not (u.startswith("wss://") or u.startswith("ws://")):
            raise ValueError(
                "Invalid url provided to WebSocket params. "
                'Expected url to start with "wss://" or "ws://". '
                f"Provided url was: {str(u)}"
            )
        return u


# pylint: disable=anomalous-backslash-in-string
class WebSocket(AbstractNode):
    """Node for ingesting data from a WebSocket.

    This node is a wrapper around the
    [websocket-client](
        https://websocket-client.readthedocs.io/en/latest/index.html
        ){:target="\_blank"} library.

    `node_params` should be a dictionary with the following keys:

        url: The WebSocket URL to connect to
        header (optional): A dictionary of headers to send to the WebSocket.
            Defaults to None.
        init_messages (optional): A list of messages to send to the WebSocket
            upon connection. Defaults to [].
        metadata (optional): A dictionary of metadata to attach to outgoing
            messages. Defaults to None.
        max_retries (optional): The maximum number of times to retry
            connecting to the WebSocket. Defaults to 30.
        retry_sleep (optional): The number of seconds to wait between retries.
            Defaults to 5.

    Secrets can be injected (from environment) into the `url`, `header`, and
    `init_messages` fields by passing a string with the following format:
    `{$SCRET_NAME}`. For example, if you have a secret named `SCRET_NAME`
    with value `SCRET_VALUE`, you can inject it into the url field by passing
    `wss://example.com?secret={$SCRET_NAME}` as the url. The connector will
    then replace `{$SCRET_NAME}` with `SCRET_VALUE` before connecting to the
    WebSocket.

    Example usage in pipeline.yml:
    ```yaml title="pipeline.yml"
    pipeline:
      nodes:
        WebSocket:
          class: aineko.extras.WebSocket
          outputs:
            - test_websocket
          node_params:
            url: "wss://example.com"
            header:
              auth: "Bearer {$SCRET_NAME}"
            init_messages:
                - {"Greeting": "Hello, world!"}
    ```
    """

    retry_count = 0

    def _pre_loop_hook(self, params: dict | None = None) -> None:
        """Initalize the WebSocket connection."""
        # Cast params to ParamsWebSocket type
        try:
            if params is not None:
                self.ws_params = ParamsWebSocket(**params)
            else:
                raise ValueError(
                    "No params provided to WebSocket connector. "
                    "Node requires at least a url param."
                )
        except Exception as err:  # pylint: disable=broad-except
            # Cast pydantic validation error to ValueError
            # so that it can be properly caught by the node
            # Note: this is required because pydantic errors
            # are not pickleable
            raise ValueError(
                "Failed to cast params to ParamsWebSocket type. "
                f"The following error occured: {str(err)}"
            ) from err
        self.ws_params.header = inject_secrets(self.ws_params.header)
        self.ws_params.init_messages = inject_secrets(
            self.ws_params.init_messages
        )
        self.ws_params.url = inject_secrets(self.ws_params.url)

        # Create the websocket subscription
        self.ws = websocket.WebSocket()
        self.create_subscription()

    def _execute(self, params: dict | None = None) -> None:
        """Polls and gets data from the WebSocket."""
        try:
            # Poll the websocket
            raw_message = self.ws.recv()
        except Exception as err:  # pylint: disable=broad-except
            # If the connection is closed, reconnect
            self.log(
                "Websocket connection closed. "
                f"Reconnecting in {str(self.ws_params.retry_sleep)} "
                f"seconds... The following error occured: {str(err)}",
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
            for dataset, producer in self.producers.items():
                if dataset != "logging":
                    producer.produce(message)
            self.retry_count = 0
        except json.decoder.JSONDecodeError as err:
            if self.retry_count < self.ws_params.max_retries:
                self.retry_count += 1
                self.log(
                    f"Failed to parse message: {str(raw_message)}. "
                    f"The following error occured: {str(err)} "
                    f"Reconnecting in {str(self.ws_params.retry_sleep)} "
                    "seconds...",
                    level="error",
                )
                time.sleep(self.ws_params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries "
                    f"({str(self.ws_params.max_retries)}). "
                    f"Failed to parse message: {str(raw_message)}. "
                    f"The following error occured: {str(err)}"
                ) from err

    def create_subscription(self) -> None:
        """Creates a subscription on the websocket."""
        try:
            self.log(f"Creating subscription to {str(self.ws_params.url)}...")
            self.ws.connect(
                url=self.ws_params.url, header=self.ws_params.header
            )  # type: ignore

            if self.ws_params.init_messages:
                # Send initialization messages
                for init_msg in self.ws_params.init_messages:
                    self.ws.send(json.dumps(init_msg))
                    message = self.ws.recv()
                    self.log(
                        f"Sent initialization message to "
                        f"{str(self.ws_params.url)}. "
                        f"Acknowledged initialization message: {str(message)}"
                    )

            ack_message = self.ws.recv()
            self.log(
                f"Subscription to {str(self.ws_params.url)} created. "
                f"Acknowledged subscription message: {str(ack_message)}"
            )

            self.retry_count = 0
        except Exception as err:  # pylint: disable=broad-except
            if self.retry_count < self.ws_params.max_retries:
                self.log(
                    "Encountered error when attempting to connect to "
                    f"{str(self.ws_params.url)}. Will retry in "
                    f"{str(self.ws_params.retry_sleep)} seconds"
                )
                self.retry_count += 1
                time.sleep(self.ws_params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries. "
                    "Failed to create subscription to "
                    f"{str(self.ws_params.url)}. "
                    f"The following error occured: {str(err)}"
                ) from err
