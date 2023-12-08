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
    default="https://dream.ap-2359264f-9cba-43ba-9ac4-ae3ba7b1d4b1.aineko.app",
    help="API url to use for the Aineko Dream API.",
)
def dream(prompt: str, api_key: str, url: str) -> None:
    """Main function generate an aineko project using Aineko Dream.\f

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
            click.echo(r.json()["status"])
        else:
            click.echo(r.text)

    except Exception as e:
        raise click.ClickException(
            f"Error connecting to Aineko Dream API at {url}: {e}"
        )
