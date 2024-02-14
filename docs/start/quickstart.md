---
description: Fastest way to get an Aineko pipeline up and running
---

# Get started with Aineko

## Technical dependencies

1. [Docker](https://www.docker.com/get-started/) or [Docker Desktop](htps://www.docker.com/products/docker-desktop)
2. [Poetry](https://python-poetry.org/docs/#installation) (a python dependency manager)
3. [Python](https://www.python.org/downloads/) (versions 3.8, 3.9, 3.10 & 3.11 are supported)
4. [Pip](https://pip.pypa.io/en/stable/installation/) (a python package manager)

??? note "Check your dependencies before starting"
    It's important to make sure you have the correct dependencies installed. The only dependency which requires a specific version is Python. The other dependencies should work with any recent version.

    Let's check each dependency one by one. You can run the following commands in your terminal to check each dependency.

    * `docker --version` should return something like `Docker version 20.10.8, build 3967b7d`
    * `python --version` should return something like `Python 3.10.12`. We recommend [pyenv](https://github.com/pyenv/pyenv) to manage versions if you have multiple versions.
    * `pip --version` should return something like `pip 23.0.1 from xxx/python3.10/site-packages/pip (python 3.10)`
    * `poetry --version` should return something like `Poetry (version 1.6.1)`

## Install Aineko

:   
    ```
    pip install aineko
    ```

??? tip "Having trouble getting the correct version of python?"

    We recommend using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv) to manage your Python versions. Once you have pyenv installed, you can run the following commands in your project directory to install one the supported versions. For example:

    ```bash
    pyenv install 3.10
    pyenv local 3.10
    python --version
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    Python 3.10.12
    ```

    Pyenv is a great tool for managing Python versions, but it can be a bit tricky to get it set up correctly. If you're having trouble, check out the [pyenv documentation](https://github.com/pyenv/pyenv?tab=readme-ov-file#usage) or [this tutorial](https://realpython.com/intro-to-pyenv/). If you're still having trouble, feel free to reach out to us on [Slack](https://join.slack.com/t/aineko-dev/shared_invite/zt-23yuq8mrl-uZavRQKGFltxLZLCqcQZaQ)!

## Create a template pipeline with the CLI

You will see the following prompts as `aineko` tries to create a project directory containing the boilerplate you need for a pipeline. Feel free to use the defaults suggested.

:   
    ```
    aineko create
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    [1/4] project_name (My Awesome Pipeline):
    [2/4] project_slug (my_awesome_pipeline):
    [3/4] project_description (Behold my awesome pipeline!):
    [4/4] pipeline_slug (test-aineko-pipeline):
    ```

## Install dependencies in the new pipeline

:   
    ```
    cd my_awesome_pipeline
    poetry install
    ```

## Start Aineko background services

:   
    ```
    poetry run aineko service start
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    Container zookeeper  Creating
    Container zookeeper  Created
    Container broker  Creating
    Container broker  Created
    Container zookeeper  Starting
    Container zookeeper  Started
    Container broker  Starting
    Container broker  Started
    ```

## Start the template pipeline

:   
    ```
    poetry run aineko run ./conf/pipeline.yml
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    INFO - Application is starting.
    INFO - Creating dataset: aineko-pipeline.sequence: {'type': 'kafka_stream'}
    INFO - All datasets created.
    INFO worker.py:1664 -- Started a local Ray instance.
    ```

## Check the data being streamed

To view messages running in one of the user-defined datasets:

:   
    ```
    poetry run aineko stream --dataset test-aineko-pipeline.test_sequence --from-beginning
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    {"timestamp": "2023-11-10 17:27:20", "dataset": "sequence", "source_pipeline": "test-aineko-pipeline", "source_node": "sequence", "message": 1}
    {"timestamp": "2023-11-10 17:27:20", "dataset": "sequence", "source_pipeline": "test-aineko-pipeline", "source_node": "sequence", "message": 2}
    ```

Alternatively, to view logs stored in the built-in `logging` dataset:

:   
    ```
    poetry run aineko stream --dataset logging --from-beginning
    ```
    ```{: .optional-language-as-class .no-copy title="Expected output"}
    {"timestamp": "2023-11-10 17:46:15", "dataset": "logging", "source_pipeline": "test-aineko-pipeline", "source_node": "sum", "message": {"log": "Received input: 1. Adding 1...", "level": "info"}}
    ```

!!! note
    User-defined datasets have the pipeline name automatically prefixed, but the special built-in dataset `logging` doesn't.


## Stop Aineko background services

:   
    ```
    poetry run aineko service stop
    ```

**So that's it to get an Aineko pipeline running. How smooth was that?**

??? question "What does the above output mean?"

    An aineko pipeline is made up of **Dataset(s)** and **Node(s).**
    A Dataset can be thought of as a mailbox. Nodes pass messages to this mailbox, that can be read by many other Nodes.

    A **Node** is an abstraction for some computation, a function if you will. At the same time a **Node** can be a reader and/or a writer of a **Dataset**. (mailbox)

    The output means that we have successfully created three datasets - **test\_sequence,** **test\_sum** and **logging**, and that we have created two nodes - **sum** and **sequence**.

To learn more about Pipeline, Datasets and Nodes, see [concepts](../developer_guide/concepts.md).

## Visualizing the pipeline

Using the Aineko CLI, you can also see the above pipeline rendered in the browser. This is helpful for quickly checking your pipeline as you iterate and evolve your architecture.

:   
    ```
    poetry run aineko visualize --browser ./conf/pipeline.yml
    ```

!!! abstract "Visualization output"
    ```mermaid
    flowchart LR
    classDef datasetClass fill:#87CEEB
    classDef nodeClass fill:#eba487
    N_sequence((sequence)):::nodeClass -->  T_test_sequence[test_sequence]:::datasetClass
    T_test_sequence[test_sequence]:::datasetClass -->  N_sum((sum)):::nodeClass
    N_sum((sum)):::nodeClass -->  T_test_sum[test_sum]:::datasetClass
    ```
