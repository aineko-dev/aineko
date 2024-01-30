# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Extra module for connecting to an HTTP endpoint."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from pydantic import BaseModel, field_validator

from aineko import AbstractNode


class ParamsHTTPPoller(BaseModel):
    """Parameters for the HTTPPoller node.

    Attributes:
        timeout (int): The number of seconds to wait for the HTTP endpoint to
            respond. Defaults to 10.
        url (str): The HTTP URL to connect to.
        headers (Optional[Dict[str, Any]]): A dictionary of headers to send to
            the HTTP endpoint. Defaults to None.
        data (Optional[Dict[str, Any]]): A dictionary of data to send to the
            HTTP endpoint. Defaults to None.
        params (Optional[Union[Dict[str, Any], List[tuple], bytes]]): A
            dictionary, list of tuples, bytes, or file-like object to send in
            the body of the HTTP request. Defaults to None.
        json_ (Optional[Dict[str, Any]]): A JSON serializable Python object to
            send in the body of the HTTP request. Defaults to None.
        auth (Optional[Tuple[str, str]]): A tuple of username and password to
            use for Basic HTTP authentication. Defaults to None.
        poll_interval (float): The number of seconds to wait between polls.
            Defaults to 5.0.
        max_retries (int): The maximum number of times to retry connecting to
            the HTTP endpoint. Defaults to -1.
        metadata (Optional[Dict[str, Any]]): A dictionary of metadata to attach
            to outgoing messages. Defaults to None.
        retry_sleep (float): The number of seconds to wait between retries.
            Defaults to 5.0.
        success_codes (List[int]): A list of HTTP status codes that indicate
            success. Defaults to
                [200, 201, 202, 203, 204, 205, 206, 207, 208, 226].

    Raises:
        ValueError: If the url is not a valid HTTP or HTTPS URL.
    """

    timeout: int = 10
    url: str
    headers: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    params: Optional[Union[Dict[str, Any], List[tuple], bytes]] = None
    json_: Optional[Dict[str, Any]] = None
    auth: Optional[Tuple[str, str]] = None
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


class HTTPPoller(AbstractNode):
    """Connects to an endpoint via HTTP or HTTPS and polls.

    This node is a wrapper around the
    [requests](
        https://docs.python-requests.org/en/master/
        ){:target="_blank"} library.

    Example usage in pipeline.yml:
    ```yaml title="pipeline.yml"
    pipeline:
      nodes:
        HTTPoller:
          class: aineko.extras.HTTPPoller
          outputs:
            - test_http
          node_params:
            url: "https://example.com"
            headers:
              auth: "Bearer {$SECRET_NAME}"
            data: {"Greeting": "Hello, world!"}
    ```

    Secrets can be injected (from environment) into the `url`, `headers`, and
    `data` fields by passing a string with the following format:
    `{$SECRET_NAME}`. For example, if you have an environment variable named
    `SECRET_NAME`that contains the value `SECRET_VALUE`, you can inject it into
    the url field by passing `https://example.com?secret={$SECRET_NAME}` as the
    url. The connector will then replace `{$SECRET_NAME}` with `SECRET_VALUE`
    before connecting to the HTTP endpoint.

    Note that the `outputs` field is required and must contain exactly one
    output dataset. The output dataset will contain the data returned by the
    endpoint.

    By default, this node will poll the endpoint every 5 seconds and timeout
    after 10 seconds. If the request fails, it will retry every 5 seconds
    forever. Status codes in the 200s are considered success codes and no
    headers, data, auth, params, or json will be attached to the request.
    """

    # Poll settings
    last_poll_time = time.time()
    retry_count = 0

    def _pre_loop_hook(self, params: Optional[Dict] = None) -> None:
        """Initializes connection to API."""
        try:
            if params is not None:
                self.http_poller_params = ParamsHTTPPoller(**params)
            else:
                raise ValueError(
                    "No params provided to HTTPPoller connector. "
                    "Node requires at least a url param."
                )
        except Exception as err:  # pylint: disable=broad-except
            # Cast pydantic validation error to ValueError
            # so that it can be properly caught by the node
            # Note: this is required because pydantic errors
            # are not pickleable
            raise ValueError(
                "Failed to cast params to ParamsHTTPPoller type. "
                f"The following error occurred: {err}"
            ) from err

        # Ensure only one output dataset is provided
        output_datasets = [
            dataset for dataset in self.producers.keys() if dataset != "logging"
        ]
        if len(output_datasets) > 1:
            raise ValueError(
                "Only one output dataset is allowed for the "
                "HTTPoller connector. "
                f"{len(output_datasets)} datasets given."
            )
        self.output_dataset = output_datasets[0]

        # Create a session
        self.log(
            f"Creating new session to endpoint {self.http_poller_params.url}."
        )
        self.session = requests.Session()

    def _execute(self, params: Optional[Dict] = None) -> None:
        """Polls and gets data from the HTTP or HTTPS endpoint.

        Raises:
            Exception: If the retry count exceeds the max retries.
        """
        # Check if it is time to poll
        if (
            time.time() - self.last_poll_time
            >= self.http_poller_params.poll_interval
        ):
            # Update the last poll time
            self.last_poll_time = time.time()

            try:
                # Poll HTTP endpoint
                response = self.session.get(
                    self.http_poller_params.url,
                    timeout=self.http_poller_params.timeout,
                    headers=self.http_poller_params.headers,
                    data=self.http_poller_params.data,
                    params=self.http_poller_params.params,
                    json=self.http_poller_params.json_,
                    auth=self.http_poller_params.auth,
                )
                # Check if the request was successful
                if (
                    response.status_code
                    not in self.http_poller_params.success_codes
                ):
                    # pylint: disable=broad-exception-raised
                    raise Exception(
                        f"Request to url {self.http_poller_params.url} "
                        "failed with status code: "
                        f"{response.status_code}"
                    )
                raw_message = response.text
            except Exception as err:  # pylint: disable=broad-except
                # If request fails, log the error and sleep
                self.log(
                    "Request failed. "
                    f"Sleeping for {self.http_poller_params.poll_interval} "
                    f"seconds. Error: {err}",
                    level="error",
                )
                time.sleep(self.http_poller_params.poll_interval)
                self.retry_count += 1
                # Reset the session
                self.log(
                    "Creating new session to HTTP endpoint "
                    f"{self.http_poller_params.url}."
                )
                self.session = requests.Session()
                return

            try:
                # Parse the message and emit to producers
                message = json.loads(raw_message)
                if self.http_poller_params.metadata is not None:
                    message = {
                        "metadata": self.http_poller_params.metadata,
                        "data": message,
                    }
                self.producers[self.output_dataset].produce(message)
                self.retry_count = 0
            except json.decoder.JSONDecodeError as err:
                if self.retry_count < self.http_poller_params.max_retries:
                    self.retry_count += 1
                    self.log(
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occurred: {err} "
                        f"Will retry in {self.http_poller_params.retry_sleep} "
                        "seconds...",
                        level="error",
                    )
                    time.sleep(self.http_poller_params.retry_sleep)
                else:
                    raise Exception(  # pylint: disable=broad-exception-raised
                        "Retry count exceeded max retries "
                        f"({self.http_poller_params.max_retries}). "
                        f"Failed to parse message: {raw_message}. "
                        f"The following error occurred: {err}"
                    ) from err
        else:
            # If it is not time to poll, sleep
            time.sleep(
                self.http_poller_params.poll_interval
                - (time.time() - self.last_poll_time)
            )
