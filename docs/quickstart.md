---
description: Fastest way to get an Aineko pipeline up and running
---
## Technical Dependencies

1. [Docker](https://www.docker.com/get-started/) or [Docker Desktop](htps://www.docker.com/products/docker-desktop)
2. [Poetry](https://python-poetry.org/docs/#installation) (a python dependency manager)
3. [Python](https://www.python.org/downloads/) (version 3.10)
4. [Pip](https://pip.pypa.io/en/stable/installation/) (a python package manager)

## Get started
### Step 0: Check your dependencies

It's important to make sure you have the correct dependencies installed. This might sound obvious, but it's easy to miss a step and we want to make sure you have a good experience with Aineko. The only dependency which requires a specific version is Python. The other dependencies should work with any recent version.

Let's check each dependency one by one. You can run the following commands in your terminal to check each dependency.

* `docker --version` should return something like `Docker version 20.10.8, build 3967b7d`
* `python --version` should return something like `Python 3.10.12` Click [here](#how-to-install-a-specific-version-of-python) if you see another version.
* `pip --version` should return something like `pip 23.0.1 from xxx/python3.10/site-packages/pip (python 3.10)`
* `poetry --version` should return something like `Poetry (version 1.6.1)`

### Step 1: Install Aineko

```pip install aineko```

### Step 2: Create a template pipeline with aineko cli

```aineko create```

You will see the following prompts as `aineko` tries to create a project directory containing the boilerplate you need for a pipeline. Feel free to use the defaults suggested!

```
  [1/4] project_name (My Awesome Pipeline):
  [2/4] project_slug (my_awesome_pipeline):
  [3/4] project_description (Behold my awesome pipeline!):
  [4/4] pipeline_slug (test-aineko-pipeline):
```

### Step 3: Install dependencies in the new pipeline

```
cd my_awesome_pipeline
poetry install
```

### Step 4: Start the Aineko background services

```
poetry run aineko service start
```

### Step 5: Start the template pipeline

```
poetry run aineko run ./conf/pipeline.yml
```

### Step 6: Check the data being streamed

To view messages running in one of the user-defined datasets:
```
poetry run aineko stream --dataset test-aineko-pipeline.test_sequence --from-start
```

Alternatively, to view logs stored in the built-in `logging` dataset:
```
poetry run aineko stream --dataset logging --from-start
```

Note: user-defined datasets have the pipeline name automatically prefixed, but the special built-in dataset `logging` does not.


### Step 7: Stop the Aineko background services

```
poetry run aineko service stop
```

**So that's it to get an Aineko pipeline running! We hope that was smooth for you!**

??? question "What does the above output mean?"

    An aineko pipeline is made up of **Dataset(s)** and **Node(s).**
    A Dataset can be thought of as a mailbox. Nodes pass messages to this mailbox, that can be read by many other Nodes.

    A **Node** is an abstraction for some computation, a function if you will. At the same time a **Node** can be a producer and/or a consumer of a **Dataset**. (mailbox)

    The output means that we have successfully created three datasets - **test\_sequence,** **test\_sum** and **logging and** two nodes - **sum** and **sequence**.

To learn more about Pipeline, Datasets and Nodes, see [concepts](./concepts.md).

### Visualizing the Pipeline

Using the aineko cli, you can also see the above pipeline rendered in the browser:

```sh
aineko visualize --browser ./conf/pipeline.yml
```

![Pipeline](./img/pipeline_visualization.png)
