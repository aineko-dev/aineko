# Contributing to Aineko Docs

Thank you for your interest in contributing to our documentation.

Here are the steps to get started quickly.

## Install Aineko from source

:   
    ```bash
    # install poetry
    $ curl -sSL https://install.python-poetry.org | python3 -

    $ git clone https://github.com/aineko-dev/aineko

    $ cd aineko && poetry install --with docs
    ```

## Make your changes to Aineko docs

Aineko raw documentation is in the form of markdown files found in the `docs` directory.

We use [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) to generate the documentation static site from markdown.

## Set up a local server to view changes live

`MkDocs` comes with a tool to display local documentation as it would on the site, allowing you to view changes as you make them. Set up a local server that automatically updates using:

:   
    ```bash
    $ poetry run mkdocs serve
    ```

Navigate to [localhost:8000](http://localhost:8000) to see the documentation site.

## Run lint

Once you're happy with your changes, run our linters to keep any additional code stylistically consistent.

:   
    ```bash
    $ make lint
    ```

## Push, make a PR and see you on GitHub.

??? question "How to make a PR?"

    To make a PR, first create and push to GitHub a branch by running the following commands.

    ```bash
    $ git checkout -b docs/<branch-name>
    $ git add .
    $ git commit -m "docs: <some descriptive message>"
    $ git push --set-upstream origin docs/<branch-name>
    ```

    Next, navigate to the [Aineko GitHub repo](https://github.com/aineko-dev/aineko/compare) and select the `docs/<branch-name>` branch in the compare box.

!!! info "Document versioning"

    On every merge to the `develop` branch, our CI automatically packages and publishes the docs under the `dev` version. Additionally, when a version of Aineko is tagged, our CI publishes that version of the docs as under that minor version (for example, the version with tag `1.2.3` will be published under `1.2`).
