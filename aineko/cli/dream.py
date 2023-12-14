# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""A wrapper around API calls to the Aineko Dream API."""

import click
import requests


@click.command()
@click.argument("prompt")
@click.argument("api-key")
@click.option(
    "-u",
    "--url",
    default="https://dream.ap-6d356ccd-bfba-4110-994a-fe164ab8bf77.aineko.app",
    help="API url to use for the Aineko Dream API.",
)
def dream(prompt: str, api_key: str, url: str) -> None:
    """Main function to generate an aineko project using Aineko Dream.\f

    Args:
        prompt: Prompt to generate a project from.
        api_key: API key to use for the Aineko Dream API.
        url: URL to use for the Aineko Dream API.
    """
    try:
        click.echo("Generating project from prompt...")

        r = requests.get(
            url=f"{url}/create/",
            params={"prompt": prompt},
            headers={"x-api-key": api_key},
            timeout=300,
        )
        click.echo(f"Received response code: {r.status_code}")
        if r.status_code == 200:
            request_id = r.json()["request_id"]
            click.echo(
                "Successfully published project to: "
                f"https://github.com/Convex-Labs/dream-catcher/tree/{request_id}. \n\n"  # pylint: disable=line-too-long
                "To create a new project from this dream, run: \n\n"
                f"aineko create --repo Convex-Labs/dream-catcher#{request_id}"
            )
        else:
            click.echo(r.text)

    except Exception as e:
        raise click.ClickException(
            f"Error connecting to Aineko Dream API at {url}: {e}"
        )
