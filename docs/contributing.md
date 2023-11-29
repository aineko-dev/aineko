# Contributing to Aineko

Thank you for your interest in contributing to [Aineko](https://github.com/aineko-dev/aineko)!

Here are the steps to get started quickly:

## Install Aineko from source

:   
    ```bash
    # install poetry
    $ curl -sSL https://install.python-poetry.org | python3 -

    $ git clone https://github.com/aineko-dev/aineko

    $ cd aineko && poetry install --with dev,test
    ```

## Make your changes to Aineko source code

## Test using Aineko pipeline

We highly encourage you to validate your changes by testing the project creation process end-to-end. This means validating the changes by running a local pipeline that uses your local aineko repository.

First, update poetry to use your local aineko repository.

:   
    ```bash
    $ poetry lock
    $ poetry install
    ```

Next, create an Aineko project in the parent directory.

:   
    ```bash
    $ poetry run aineko create --output-dir ../
    ```

Next, update the create aineko project to use the local aineko repository. Go to `../my-awesome-pipeline/pyproject.toml` and update the following line.

:   
    ```bash title="pyproject.toml" linenums="8" hl_lines="3"
    [tool.poetry.dependencies]
    python = ">=3.10,<3.11"
    aineko = { path = "<path/to/aineko/git/repo>", develop=true}
    ```

Test if your changes worked by running the aineko pipeline and any other testing methods that are relevant.

## Run lints and tests

Finally, after you have make all the changes, it is good to validate that you adhered to the style guide and you did not break anything.

:   
    ```bash
    # Within aineko git repository
    make lint
    make unit-test
    make integration-test
    ```

## Push, make a pull request and see you on GitHub
