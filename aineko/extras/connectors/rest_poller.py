# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to a REST endpoint."""

import json
import time
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, field_validator

from aineko import AbstractNode


class ParamsRESTPoller(BaseModel):
    """Connector params for REST model."""

    timeout: int = 10
    url: str
    headers: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    poll_interval: float = 5.0
    max_retries: int = -1
    metadata: Optional[Dict[str, Any]] = None
    retry_sleep: float = 5
    success_codes: List[int] = [
        200,
        201,
        202,
        203,
        204,
        205,
        206,
        207,
        208,
        226,
    ]

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
    """Connects to an REST endpoint via HTTP or HTTPS and polls.

    This node is a wrapper around the
    [requests](
        https://docs.python-requests.org/en/master/
        ){:target="_blank"} library.

    `node_params` should be a dictionary with the following keys:

            url: The REST URL to connect to
            headers (optional): A dictionary of headers to send to the REST
                endpoint. Defaults to None.
            data (optional): A dictionary of data to send to the REST endpoint.
                Defaults to None.
            poll_interval (optional): The number of seconds to wait between
                polls. Defaults to 5.
            max_retries (optional): The maximum number of times to retry
                connecting to the REST endpoint. Defaults to -1.
            retry_sleep (optional): The number of seconds to wait between
                retries. Defaults to 5.
            metadata (optional): A dictionary of metadata to attach to outgoing
                messages. Defaults to None.
            success_codes (optional): A list of HTTP status codes that indicate
                success. Defaults to
                    [200, 201, 202, 203, 204, 205, 206, 207, 208, 226].

    Secrets can be injected (from environment) into the `url`, `headers`, and
    `data` fields by passing a string with the following format:
    `{$SECRET_NAME}`. For example, if you have a secret named `SECRET_NAME`
    that contains the value `SECRET_VALUE`, you can inject it into the url
    field by passing `https://example.com?secret={$SECRET_NAME}` as the url.
    The connector will then replace `{$SECRET_NAME}` with `SECRET_VALUE` before
    connecting to the REST endpoint.

    Example usage in pipeline.yml:
    ```yaml title="pipeline.yml"
    pipeline:
      nodes:
        RestPoller:
          class: aineko.extras.RestPoller
          outputs:
            - test_rest
          node_params:
            url: "https://example.com"
            headers:
              auth: "Bearer {$SECRET_NAME}"
            data: {"Greeting": "Hello, world!"}
    ```

    Note that the `outputs` field is required and must contain exactly one
    output dataset. The output dataset will contain the data returned by the
    REST endpoint.

    By default, this node will poll the REST endpoint every 5 seconds. This can
    be changed by setting the `poll_interval` field in `node_params`. If the
    REST endpoint is not expected to be available at all times, it is
    recommended to increase `poll_interval` to reduce the number of requests
    sent to the endpoint.

    By default, this node will retry connecting to the REST endpoint forever
    if the connection fails. This can be changed by setting the `max_retries`
    field in `node_params`. If the REST endpoint is not expected to be
    available at all times, it is recommended to set `max_retries` to a
    finite number to prevent the node from retrying forever.

    By default, this node will retry connecting to the REST endpoint every 5
    seconds if the connection fails. This can be changed by setting the
    `retry_sleep` field in `node_params`. If the REST endpoint is not expected
    to be available at all times, it is recommended to increase `retry_sleep`
    to reduce the number of requests sent to the endpoint.

    By default, this node will consider any HTTP status code in the 200s to be
    a success code. This can be changed by setting the `success_codes` field
    in `node_params`. If the REST endpoint returns a non-200 status code on
    success, it is recommended to add the status code to the `success_codes`
    list.

    By default, this node will not attach headers or data to the request. This
    can be changed by setting the `headers` and `data` fields in `node_params`.
    If the REST endpoint requires headers or data to be sent, it is
    you should set the `headers` and `data` fields in `node_params`.

    By default, this node will timeout after 10 seconds. This can be changed
    by setting the `timeout` field in `node_params`. If the REST endpoint is
    expected to take a long time to respond, it is recommended to increase
    `timeout` to prevent the node from timing out.
    """

    # Poll settings
    last_poll_time = time.time()
    retry_count = 0

    def _pre_loop_hook(self, params: Optional[Dict] = None) -> None:
        """Initializes connection to API."""
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

    def _execute(self, params: Optional[Dict] = None) -> None:
        """Polls and gets data from the HTTP or HTTPS endpoint.

        Raises:
            Exception: If the retry count exceeds the max retries.
        """
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
                self.retry_count += 1
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
                    raise Exception(  # pylint: disable=broad-exception-raised
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
