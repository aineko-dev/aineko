# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a WebSocket."""

import time
import json
from typing import Dict, Any, Optional
import os

from dotenv import load_dotenv
import requests
from pydantic import BaseModel, field_validator

from aineko import AbstractNode
from aineko.utils.secrets import dict_inject_secrets, str_inject_secrets

class ParamsHTTPS(BaseModel):
    """Connector params for WebSocket model."""

    timeout: Optional[int] = 10
    url: str
    headers: Optional[Dict[str, Any]] = None

    @field_validator("url")
    def supported_url(cls, u: str) -> str:  # pylint: disable=no-self-argument
        """Validates that the url is a valid WebSocket URL."""
        if not u.startswith("https://"):
            raise ValueError(
                "Invalid url provided to HTTPS params. "
                "Expected url to start with \"https://\". "
                f"Provided url was: {u}"
            )
        return u

    poll_interval = Optional[int] = 1
    poll_throttle = Optional[float] = 0.1
    max_retries: Optional[int] = 30


class GetHTTPS(AbstractNode):
    """Connects to an REST endpoint via HTTPS."""

    def _pre_loop_hook(self, params: Dict[str, Any] = None):
        """Initializes connection to API."""
        # Load the API keys from the .env file, used locally
        load_dotenv()

        # Cast params to ParamsHTTPS type
        self.params_https = ParamsHTTPS(**params)
        # TODO: Can we inject secrets via the Pydantic class?
        self.params_https.headers = dict_inject_secrets(self.params_https.headers)
        self.params_https.url = str_inject_secrets(self.params_https.url)

        # Poll settings
        self.last_poll_time = time.time()
        self.retry_count = 0

    def _execute(self, params: Dict[str, Any] = None):
        """Polls and gets data from the WebSocket."""
        # Check if it is time to poll
        if time.time() - self.last_poll_time >= self.params_https.poll_interval:
            # Update the last poll time
            self.last_poll_time = time.time()

            try:
                # Poll REST api
                response = requests.get(
                    self.params_https.url,
                    timeout=self.params_https.timeout,
                    headers=self.params_https.headers
                    )
                # Check if the request was successful
                if response.status_code != 200:
                    # pylint: disable=broad-exception-raised
                    raise Exception(
                        f"Request to url {self.params_https.url} "
                        "failed with status code: "
                        f"{response.status_code}"
                    )
                raw_message = response.text
            except Exception as err:  # pylint: disable=broad-except
                # If request fails, log the error and sleep
                self.log(
                    "Request failed. "
                    f"Sleeping for {self.params_https.poll_interval} seconds. "
                    f"Error: {err}",
                    level="error",
                )
                return

            try:
                # Parse the message and emit to producers
                message = json.loads(raw_message)
                for dataset, producer in self.producers.items():
                    if dataset != "logging":
                        producer.produce(message)
                self.retry_count = 0
            except json.decoder.JSONDecodeError as err:
                if self.retry_count < self.params_https.max_retries:
                    self.retry_count += 1
                    self.log(
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occured: {err} "
                        f"Will retry in {self.params_https.retry_sleep} "
                        "seconds...",
                        level="error",
                    )
                    time.sleep(self.params_https_wss.retry_sleep)
                else:
                    raise ValueError(
                        "Retry count exceeded max retries "
                        f"({self.params_https.max_retries}). "
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occured: {err}"
                    ) from err
        else:
            # If it is not time to poll, sleep
            time.sleep(self.poll_throttle)