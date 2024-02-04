# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A wrapper around API calls to the Aineko Dream API."""

import time

import click
import requests


def create_project_from_prompt(
    api_key: str,
    url: str,
    prompt: str,
) -> str:
    """Create a project from a prompt.

    Args:
        api_key: API key to use for the Aineko Dream API.
        url: URL to use for the Aineko Dream API.
        prompt: Prompt to generate a project from.

    Returns:
        request_id: Request ID for the project generation.

    Raises:
        click.ClickException: If there is an error generating the project.
    """
    try:
        r = requests.get(
            url=f"{url}/create",
            params={"prompt": prompt},
            headers={"x-api-key": api_key},
            timeout=60,
        )
        click.echo(f"Received response code: {r.status_code}")
        if r.status_code == 202:
            return r.json()["request_id"]

        else:
            raise click.ClickException(
                f"received status code {r.status_code} with message: {r.text}"
            )

    except Exception as e:
        raise click.ClickException(
            f"Error generating project at Aineko Dream API at {url}: {e}"
        )


def check_request_status(
    api_key: str,
    url: str,
    request_id: str,
    timeout: int = 300,
) -> str:
    """Check the status of a request.

    Args:
        api_key: API key to use for the Aineko Dream API.
        url: URL to use for the Aineko Dream API.
        request_id: Request ID to check status for.
        timeout: Seconds to wait for successful project generation before timing out.

    Returns:
        Status message.

    Raises:
        click.ClickException: If there is an error checking the request status.
    """
    start_time = time.time()
    while True:
        time_elapsed = time.time() - start_time
        if time_elapsed > timeout:
            raise click.ClickException(
                "Timed out waiting for project to generate. "
            )

        try:
            r = requests.get(
                url=f"{url}/result",
                params={"request_id": request_id},
                headers={"x-api-key": api_key},
                timeout=60,
            )
        except Exception as e:
            raise click.ClickException(
                f"Error checking request status at Aineko Dream API at {url}: {e}"
            )

        if r.status_code == 204:
            click.echo(
                f"Project generating... (time elapsed: {int(time_elapsed)}s)"
            )
            time.sleep(10)
            continue

        elif r.status_code == 200:
            return (
                "Successfully published project to: "
                f"https://github.com/Convex-Labs/dream-catcher/tree/{request_id}. \n\n"  # pylint: disable=line-too-long
                "To create a new project from this dream, run: \n\n"
                f"aineko create --repo Convex-Labs/dream-catcher#{request_id}"
            )

        else:
            raise click.ClickException(
                "Received unexpected status code "
                f"{r.status_code} with message: {r.text}"
            )


@click.group()
def dream() -> None:
    """Aineko Dream CLI."""
    pass


@dream.command()
@click.argument("request-id")
@click.option(
    "-k",
    "--api-key",
    help="API key to use for the Aineko Dream API.",
)
@click.option(
    "-u",
    "--url",
    help="API url to use for the Aineko Dream API.",
)
@click.option(
    "-t",
    "--timeout",
    default=300,
    help=(
        "Seconds to wait for successful project generation before "
        "timing out. Will poll status every 10 seconds."
    ),
)
def check(request_id: str, api_key: str, url: str, timeout: int) -> None:
    """Check the status of a project generation request.

    Args:
        request_id: Request ID to check status for.
        api_key: API key to use for the Aineko Dream API.
        url: URL to use for the Aineko Dream API.
        timeout: Seconds to wait for successful project generation before timing out.
    """
    status = check_request_status(api_key, url, request_id, timeout)
    click.echo(status)


@dream.command()
@click.argument("prompt")
@click.option(
    "-k",
    "--api-key",
    help="API key to use for the Aineko Dream API.",
)
@click.option(
    "-u",
    "--url",
    help="API url to use for the Aineko Dream API.",
)
def create(
    prompt: str = None,
    api_key: str = None,
    url: str = "https://dream.ap-6d356ccd-bfba-4110-994a-fe164ab8bf77.aineko.app",
) -> None:
    """Command to generate an aineko project using Aineko Dream.\f

    Args:
        prompt: Prompt to generate a project from.
        api_key: API key to use for the Aineko Dream API.
        url: URL to use for the Aineko Dream API.
    """
    click.echo("Generating project from prompt...")
    request_id = create_project_from_prompt(api_key, url, prompt)
    click.echo(f"Successfully generated project with request ID: {request_id}.")

    status = check_request_status(api_key, url, request_id)
    click.echo(status)
