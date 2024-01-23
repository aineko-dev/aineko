# Contributing to Aineko

Thank you for your interest in contributing to [Aineko](https://github.com/Aineko-dev/Aineko)!

Here are the steps to get started quickly:

## Install Aineko from source

First, make sure you have poetry installed on your system if not already installed.

:   
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

Then, install the source code for Aineko on your local system.

:   
    ```bash
    git clone https://github.com/aineko-dev/aineko
    cd aineko && poetry install --with dev,test,docs
    ```

## Make your changes to Aineko source code

Update Aineko on your local system.

## Test using Aineko pipeline

We highly encourage you to validate your changes by testing the project creation process end-to-end. This means validating the changes by running a local pipeline that uses your local Aineko repository.

First, update poetry to use your local Aineko repository.

:   
    ```bash
    poetry lock
    poetry install
    ```

Next, create an Aineko project in the parent directory.

:   
    ```bash
    poetry run aineko create --output-dir ../
    ```

Next, update the create Aineko project to use the local Aineko repository. Go to `../my-awesome-pipeline/pyproject.toml` and update the following line.

:   
    ```bash title="pyproject.toml" linenums="8" hl_lines="3"
    [tool.poetry.dependencies]
    python = ">=3.8,<3.12"
    aineko = { path = "<path/to/Aineko/git/repo>", develop=true}
    ```

Test if your changes worked by running the Aineko pipeline and any other testing methods that are relevant.

## Run lints and tests

Finally, after making all the changes, it's good to validate that you adhered to the style guide and you didn't break anything.

:   
    ```bash
    # Within aineko git repository
    make lint
    make unit-test
    make integration-test
    ```

## Update Aineko docs

Aineko raw documentation is in the form of markdown files found in the `docs` directory.

Aineko uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) to generate the documentation static site from markdown.

## Set up a local server to view changes live

`MkDocs` comes with a tool to display local documentation as it would on the site, allowing you to view changes as you make them. Set up a local server that automatically updates using:

:   
    ```bash
    poetry run mkdocs serve
    ```

Navigate to [localhost:8000](http://localhost:8000) to see the documentation site.

## Run lint

Once you're happy with your changes, run the linters to keep any additional code stylistically consistent. You will need to install [vale](https://vale.sh/) (a linter for prose) first. Installation instructions  can be found [here](https://vale.sh/docs/vale-cli/installation/#package-managers).

:   
    ```bash
    make lint
    make lint-docs
    ```

## Make a pull request

??? question "How to make a PR?"

    To make a PR, first create and push to GitHub a branch by running the following commands.

    ```bash
    git checkout -b docs/<branch-name>
    git add .
    git commit -m "docs: <some descriptive message>"
    git push --set-upstream origin docs/<branch-name>
    ```

    Next, navigate to the [Aineko GitHub repo](https://github.com/Aineko-dev/Aineko/compare) and select the `docs/<branch-name>` branch in the compare box.

!!! info "Document versioning"

    On every merge to the `develop` branch, our CI automatically packages and publishes the docs under the `dev` version. Additionally, when a version of Aineko is tagged, our CI publishes that version of the docs as under that minor version (for example, the version with tag `1.2.3` will be published under `1.2`).
