# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a HTTPS endpoint."""

import time
import json
from typing import Dict, Any, Optional

import requests
from pydantic import BaseModel, field_validator

from aineko import AbstractNode
from aineko.extras.connectors.secrets import inject_secrets

class ParamsREST(BaseModel):
    """Connector params for REST model."""

    timeout: int = 10
    url: str
    headers: Optional[Dict[str, Any]] = None
    poll_interval: int = 5
    poll_throttle: float = 0.1
    max_retries: int = 30
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("url")
    @classmethod
    def supported_url(cls, url: str) -> str:  # pylint: disable=no-self-argument
        """Validates that the url is a valid HTTPS URL."""
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError(
                "Invalid url provided to HTTPS params. "
                "Expected url to start with \"https://\". "
                f"Provided url was: {url}"
            )
        return url


class REST(AbstractNode):
    """Connects to an REST endpoint via HTTPS."""

    # Poll settings
    last_poll_time = time.time()
    retry_count = 0

    def _pre_loop_hook(self, params: dict | None = None) -> None:
        """Initializes connection to API."""
        # Cast params to ParamsREST type
        try:
            if params is not None:
                self.rest_params = ParamsREST(**params)
            else:
                raise ValueError(
                    "No params provided to REST connector. "
                    "Node requires at least a url param."
                )
        except Exception as err:  # pylint: disable=broad-except
            # Cast pydantic validation error to ValueError
            # so that it can be properly caught by the node
            # Note: this is required because pydantic errors
            # are not pickleable
            raise ValueError(
                "Failed to cast params to ParamsREST type. "
                f"The following error occurred: {err}"
            ) from err
        self.rest_params.headers = inject_secrets(self.rest_params.headers)
        self.rest_params.url = inject_secrets(self.rest_params.url)

        # Create a session
        self.session = requests.Session()

    def _execute(self, params: dict | None = None) -> None:
        """Polls and gets data from the HTTPS endpoint."""
        # Check if it is time to poll
        if time.time() - self.last_poll_time >= self.rest_params.poll_interval:
            # Update the last poll time
            self.last_poll_time = time.time()

            try:
                # Poll REST api
                response = self.session.get(
                    self.rest_params.url,
                    timeout=self.rest_params.timeout,
                    headers=self.rest_params.headers,
                    )
                # Check if the request was successful
                if response.status_code != 200:
                    # pylint: disable=broad-exception-raised
                    raise Exception(
                        f"Request to url {self.rest_params.url} "
                        "failed with status code: "
                        f"{response.status_code}"
                    )
                raw_message = response.text
            except Exception as err:  # pylint: disable=broad-except
                # If request fails, log the error and sleep
                self.log(
                    "Request failed. "
                    f"Sleeping for {self.rest_params.poll_interval} seconds. "
                    f"Error: {err}",
                    level="error",
                )
                time.sleep(self.rest_params.poll_interval)
                # Reset the session
                self.session = requests.Session()
                return

            try:
                # Parse the message and emit to producers
                message = json.loads(raw_message)
                if self.rest_params.metadata is not None:
                    message = {
                        "metadata": self.rest_params.metadata,
                        "data": message,
                    }
                for dataset, producer in self.producers.items():
                    if dataset != "logging":
                        producer.produce(message)
                self.retry_count = 0
            except json.decoder.JSONDecodeError as err:
                if self.retry_count < self.rest_params.max_retries:
                    self.retry_count += 1
                    self.log(
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occured: {err} "
                        f"Will retry in {self.rest_params.retry_sleep} "
                        "seconds...",
                        level="error",
                    )
                    time.sleep(self.rest_params.retry_sleep)
                else:
                    raise ValueError(
                        "Retry count exceeded max retries "
                        f"({self.rest_params.max_retries}). "
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occured: {err}"
                    ) from err
        else:
            # If it is not time to poll, sleep
            time.sleep(self.rest_params.poll_throttle)
