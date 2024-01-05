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


class WSS(AbstractNode):
    """Connector for a websocket."""

    retry_count = 0

    def _pre_loop_hook(self, params: dict | None = None) -> None:
        """Initalize the WebSocket connection."""
        # Cast params to ParamsWSS type
        try:
            if params is not None:
                self.wss_params = ParamsWSS(**params)
            else:
                raise ValueError(
                    "No params provided to WSS connector. "
                    "Node requires at least a url param."
                )
        except Exception as err:  # pylint: disable=broad-except
            # Cast pydantic validation error to ValueError
            # so that it can be properly caught by the node
            # Note: this is required because pydantic errors
            # are not pickleable
            raise ValueError(
                "Failed to cast params to ParamsWSS type. "
                f"The following error occured: {str(err)}"
            ) from err
        self.wss_params.header = inject_secrets(self.wss_params.header)
        self.wss_params.init_messages = inject_secrets(
            self.wss_params.init_messages
        )
        self.wss_params.url = inject_secrets(self.wss_params.url)

        # Create the websocket subscription
        self.ws = websocket.WebSocket()
        self.create_subscription()

    def _execute(self, params: dict) -> None:
        """Polls and gets data from the WebSocket."""
        try:
            # Poll the websocket
            raw_message = self.ws.recv()
        except Exception as err:  # pylint: disable=broad-except
            # If the connection is closed, reconnect
            self.log(
                "Websocket connection closed. "
                f"Reconnecting in {str(self.wss_params.retry_sleep)} "
                f"seconds... The following error occured: {str(err)}",
                level="error",
            )
            time.sleep(self.wss_params.retry_sleep)
            self.create_subscription()
            return

        try:
            # Parse the message and emit to producers
            message = json.loads(raw_message)
            if self.wss_params.metadata is not None:
                message = {
                    "metadata": self.wss_params.metadata,
                    "data": message,
                }
            for dataset, producer in self.producers.items():
                if dataset != "logging":
                    producer.produce(message)
            self.retry_count = 0
        except json.decoder.JSONDecodeError as err:
            if self.retry_count < self.wss_params.max_retries:
                self.retry_count += 1
                self.log(
                    f"Failed to parse message: {str(raw_message)}. "
                    f"The following error occured: {str(err)} "
                    f"Reconnecting in {str(self.wss_params.retry_sleep)} "
                    "seconds...",
                    level="error",
                )
                time.sleep(self.wss_params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries "
                    f"({str(self.wss_params.max_retries)}). "
                    f"Failed to parse message: {str(raw_message)}. "
                    f"The following error occured: {str(err)}"
                ) from err

    def create_subscription(self) -> None:
        """Creates a subscription on the websocket."""
        try:
            self.log(f"Creating subscription to {str(self.wss_params.url)}...")
            self.ws.connect(
                url=self.wss_params.url, header=self.wss_params.header
            )  # type: ignore

            if self.wss_params.init_messages:
                # Send initialization messages
                for init_msg in self.wss_params.init_messages:
                    self.ws.send(json.dumps(init_msg))
                    message = self.ws.recv()
                    self.log(
                        f"Sent initialization message to "
                        f"{str(self.wss_params.url)}. "
                        f"Acknowledged initialization message: {str(message)}"
                    )

            ack_message = self.ws.recv()
            self.log(
                f"Subscription to {str(self.wss_params.url)} created. "
                f"Acknowledged subscription message: {str(ack_message)}"
            )

            self.retry_count = 0
        except Exception as err:  # pylint: disable=broad-except
            if self.retry_count < self.wss_params.max_retries:
                self.log(
                    "Encountered error when attempting to connect to "
                    f"{str(self.wss_params.url)}. Will retry in "
                    f"{str(self.wss_params.retry_sleep)} seconds"
                )
                self.retry_count += 1
                time.sleep(self.wss_params.retry_sleep)
                self.create_subscription()
            else:
                raise ValueError(
                    "Retry count exceeded max retries. "
                    "Failed to create subscription to "
                    f"{str(self.wss_params.url)}. "
                    f"The following error occured: {str(err)}"
                ) from err
