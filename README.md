# Aineko

Aineko is a Python framework for building data applications.

With Aineko, you seamlessly bring data into any product and iterate quickly. Whether you're an individual developer or part of a larger team, Aineko helps you rapidly build scalable, maintainable, and fast data applications.

Under the hood, Aineko automatically configures tooling needed for production-ready data apps, like message brokers, distributed compute, and more. This allows you to focus on building your application instead of spending time with configuration and infrastructure.

## Documentation

For full documentation visit: https://docs.aineko.dev/

## Quick Start

### Technical Dependencies

1. [Docker](https://www.docker.com/get-started/) or [Docker Desktop](htps://www.docker.com/products/docker-desktop)
2. [Poetry](https://python-poetry.org/docs/#installation) (a python dependency manager)
3. [Python](https://www.python.org/downloads/) (version 3.10)
4. [Pip](https://pip.pypa.io/en/stable/installation/) (a python package manager)

### Steps to get started
#### Step 0: Check your dependencies

It's important to make sure you have the correct dependencies installed. This might sound obvious, but it's easy to miss a step and we want to make sure you have a good experience with Aineko. The only dependency which requires a specific version is Python. The other dependencies should work with any recent version.

Let's check each dependency one by one. You can run the following commands in your terminal to check each dependency.

* `docker --version` should return something like `Docker version 20.10.8, build 3967b7d`
* `python --version` should return something like `Python 3.10.12` Click [here](#how-to-install-a-specific-version-of-python) if you see another version.
* `pip --version` should return something like `pip 23.0.1 from xxx/python3.10/site-packages/pip (python 3.10)`
* `poetry --version` should return something like `Poetry (version 1.6.1)`

#### Step 1: Install Aineko

`pip install aineko`

#### Step 2: Create a template pipeline with aineko cli

`aineko create`

You will see the following prompts as `aineko` tries to create a project directory containing the boilerplate you need for a pipeline. Feel free to use the defaults suggested!

```
  [1/4] project_name (My Awesome Pipeline):
  [2/4] project_slug (my_awesome_pipeline):
  [3/4] project_description (Behold my awesome pipeline!):
  [4/4] pipeline_slug (test-aineko-pipeline):
```

#### Step 3: Install dependencies in the new pipeline

```
cd my_awesome_pipeline
poetry install
```

#### Step 4: Start the Aineko background services

`poetry run aineko service start`

#### Step 5: Start the template pipeline

`poetry run aineko run ./conf/pipeline.yml`

#### Step 6: Check the data being streamed

To view messages running in one of the user-defined datasets:

```
poetry run aineko stream --dataset test-aineko-pipeline.test_sequence --from-start
```

alternatively, to view logs stored in the built-in `logging` dataset:
```
poetry run aineko stream --dataset logging --from-start
```

Note: user-defined datasets have the pipeline name automatically prefixed, but the special built-in dataset `logging` does not.

#### Step 7: Stop the Aineko background services

`poetry run aineko service stop`


## Troubleshooting
### How to install a specific version of Python
We recommend using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv) to manage your Python versions. Once you have pyenv installed, you can run the following commands to install Python 3.10.
1. `pyenv install 3.10` to install Python 3.10
2. In your project directory, run the following command to set the local Python version to 3.10: `pyenv local 3.10`
   This will create a `.python-version` file in your project directory which will tell pyenv to (automagically) use Python 3.10 when you're in that directory.
3. Check that you're now using the correct version of Python by running `python --version`. You should see something like `Python 3.10.12`.
4. You're all set! You can now proceed with [step 1](#step-1-install-aineko) of the quick start guide.

Pyenv is a great tool for managing Python versions, but it can be a bit tricky to get it set up correctly. If you're having trouble, check out the [pyenv documentation](https://github.com/pyenv/pyenv?tab=readme-ov-file#usage) or [this tutorial](https://realpython.com/intro-to-pyenv/). If you're still having trouble, feel free to reach out to us on [Slack](https://join.slack.com/t/aineko-dev/shared_invite/zt-23yuq8mrl-uZavRQKGFltxLZLCqcQZaQ)!


## Examples

To see some examples of Aineko in action visit: https://docs.aineko.dev/examples

- [Aineko Dream](https://github.com/aineko-dev/aineko-dream)
- More coming soon...

## Contributing

If you're interested in contributing to Aineko, follow this guide: https://docs.aineko.dev/contributing-to-aineko
