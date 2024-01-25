# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a REST endpoint."""

import json
import time
from typing import Any, Dict, Optional, List

import requests
from pydantic import BaseModel, field_validator

from aineko import AbstractNode


class ParamsRESTPoller(BaseModel):
    """Connector params for REST model."""

    timeout: int = 10
    url: str
    headers: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    poll_interval: int = 5
    max_retries: int = 30
    metadata: Optional[Dict[str, Any]] = None
    retry_sleep: float = 5
    success_codes: Optional[List[int]] = list(range(200, 300))

    @field_validator("url")
    @classmethod
    def supported_url(cls, url: str) -> str:
        """Validates that the url is a valid HTTP or HTTPS URL."""
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError(
                "Invalid url provided to HTTPS params. "
                'Expected url to start with "https://". '
                f"Provided url was: {url}"
            )
        return url


class RESTPoller(AbstractNode):
    """Connects to an REST endpoint via HTTP or HTTPS and polls."""

    # Poll settings
    last_poll_time = time.time()
    retry_count = 0

    def _pre_loop_hook(self, params: dict | None = None) -> None:
        """Initializes connection to API."""
        # Cast params to ParamsREST type
        try:
            if params is not None:
                self.rest_params = ParamsRESTPoller(**params)
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

        # Ensure only one output dataset is provided
        output_datasets = [
            dataset for dataset in self.producers.keys() if dataset != "logging"
            ]
        if len(output_datasets) > 1:
            raise ValueError(
                "Only one output dataset is allowed for the "
                "RESTPoller connector. "
                f"{len(output_datasets)} datasets given."
            )
        self.output_dataset = output_datasets[0]

        # Create a session
        self.log(
            f"Creating new session to REST endpoint {self.rest_params.url}."
        )
        self.session = requests.Session()

    def _execute(self, params: dict | None = None) -> None:
        """Polls and gets data from the HTTP or HTTPS endpoint."""
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
                    data=self.rest_params.data,
                )
                # Check if the request was successful
                if response.status_code not in self.rest_params.success_codes:
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
                self.log(
                    "Creating new session to REST endpoint "
                    f"{self.rest_params.url}."
                )
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
                self.producers[self.output_dataset].produce(message)
                self.retry_count = 0
            except json.decoder.JSONDecodeError as err:
                if self.retry_count < self.rest_params.max_retries:
                    self.retry_count += 1
                    self.log(
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occurred: {err} "
                        f"Will retry in {self.rest_params.retry_sleep} "
                        "seconds...",
                        level="error",
                    )
                    time.sleep(self.rest_params.retry_sleep)
                else:
                    raise Exception(  # pylint: disable=broad-except
                        "Retry count exceeded max retries "
                        f"({self.rest_params.max_retries}). "
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occurred: {err}"
                    ) from err
        else:
            # If it is not time to poll, sleep
            time.sleep(
                self.rest_params.poll_interval
                - (time.time() - self.last_poll_time)
            )
