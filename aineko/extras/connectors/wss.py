# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a WebSocket."""

import json
import time
from typing import Any, Dict, List, Optional

import websocket
from pydantic import BaseModel, field_validator

from aineko import AbstractNode
from aineko.utils.secrets import inject_secrets


class ParamsWSS(BaseModel):
    """Connector params for WebSocket model."""

    max_retries: Optional[int] = 30
    retry_sleep: Optional[int] = 5
    url: str
    header: Optional[Dict[str, str]] = None
    init_messages: Optional[List[Any]] = []
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("url")
    def supported_url(cls, u: str) -> str:  # pylint: disable=no-self-argument
        """Validates that the url is a valid WebSocket URL."""
        if not u.startswith("wss://") or u.startswith("ws://"):
            raise ValueError(
                "Invalid url provided to WebSocket params. "
                'Expected url to start with "wss://" or "ws://". '
                f"Provided url was: {u}"
            )
        return u


class WSS(AbstractNode):
    """Connector for a websocket."""

    def _pre_loop_hook(self, params: Dict[str, Any] = None) -> None:
        """Initalize the WebSocket connection."""
        # Cast params to ParamsWSS type
        try:
            self.params = ParamsWSS(**params)
        except Exception as err:  # pylint: disable=broad-except
            raise ValueError(
                "Failed to cast params to ParamsWSS type. "
                f"The following error occured: {err}"
            ) from err
        self.params.header = inject_secrets(self.params.header)
        self.params.init_messages = inject_secrets(self.params.init_messages)
        self.params.url = inject_secrets(self.params.url)

        # Setup the websocket node parameters
        self.retry_count = 0

        # Create the websocket subscription
        self.ws = websocket.WebSocket()
        self.create_subscription()

    def _execute(self, params: Dict[str, Any] = None) -> None:
        """Polls and gets data from the WebSocket."""
        try:
            # Poll the websocket
            raw_message = self.ws.recv()
        except Exception as err:  # pylint: disable=broad-except
            # If the connection is closed, reconnect
            self.log(
                "Websocket connection closed. "
                f"Reconnecting in {self.params.retry_sleep} seconds... "
                f"The following error occured: {err}",
                level="error",
            )
            time.sleep(self.params.retry_sleep)
            self.create_subscription()
            return

        try:
            # Parse the message and emit to producers
            message = json.loads(raw_message)
            if self.params.metadata is not None:
                message = {
                    "metadata": self.params.metadata,
                    "data": message,
                }
            for dataset, producer in self.producers.items():
                if dataset != "logging":
                    producer.produce(message)
            self.retry_count = 0
        except json.decoder.JSONDecodeError as err:
            if self.retry_count < self.params.max_retries:
                self.retry_count += 1
                self.log(
                    f"Failed to parse message: {raw_message}. "
                    f"The following error occured: {err} "
                    f"Reconnecting in {self.params.retry_sleep} seconds...",
                    level="error",
                )
                time.sleep(self.params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries "
                    f"({self.params.max_retries}). "
                    f"Failed to parse message: {raw_message}. "
                    f"The following error occured: {err}"
                ) from err

    def create_subscription(self) -> None:
        """Creates a subscription on the websocket."""
        try:
            self.log(f"Creating subscription to {self.params.url}...")
            self.ws.connect(url=self.params.url, header=self.params.header)

            if self.params.init_messages:
                # Send initialization messages
                for init_msg in self.params.init_messages:
                    self.ws.send(json.dumps(init_msg))
                    message = self.ws.recv()
                    self.log(
                        f"Sent initialization message to {self.params.url}. "
                        f"Acknowledged initialization message: {message}"
                    )

            ack_message = self.ws.recv()
            self.log(
                f"Subscription to {self.params.url} created. "
                f"Acknowledged subscription message: {ack_message}"
            )

            self.retry_count = 0
        except Exception as err:  # pylint: disable=broad-except
            if self.retry_count < self.params.max_retries:
                self.log(
                    "Encountered error when attempting to connect to "
                    f"{self.params.url}. Will retry in "
                    f"{self.params.retry_sleep} seconds"
                )
                self.retry_count += 1
                time.sleep(self.params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    f"Retry count exceeded max retries. "
                    f"Failed to create subscription to {self.params.url}. "
                    f"The following error occured: {err}"
                ) from err
