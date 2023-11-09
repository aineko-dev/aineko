---
description: A closer look into how a pipeline is defined and some CLI commands
---

# Aineko Project

!!! note
    This is a continuation of the [previous section (Quick Start)](../quickstart.md). Before starting, make sure you have already created a template project using `aineko create`.

## Directory contents

```
.
├── README.md
├── conf
│   └── pipeline.yml
├── docker-compose.yml
├── my_awesome_pipeline
│   ├── __init__.py
│   ├── config.py
│   └── nodes.py
├── poetry.lock
├── pyproject.toml
└── tests
    ├── __init__.py
    └── test_nodes.py
```

This is how the boilerplate directory look - many of these files are boilerplate files to make things work.

Let's zoom in on the more interesting files to take note of:

1. **`conf/pipeline.yml`** - This contains your pipeline definition that you are expected to modify to define your own pipeline. It is defined in yaml.
2. **`my_awesome_pipeline/nodes.py`** - Remember how nodes are abstractions for computations? These nodes are implemented in Python. You do not have to strictly define them in this file. You can define them anywhere you like within the directory as long as you reference them correctly in `pipeline.yml`.
3. **`docker-compose.yml`** - When we invoke `aineko run` , datasets has to be initialised - which means that we need to create Kafka topics. This file contains the image we need to create containers from, as well as other configurations like env var and network settings. _You typically do not have to change this file._

## Defining a Pipeline

Pipelines are defined using a `.yml` file that contains specific keys. In this configuration file, you can assemble a pipeline from nodes and datasets.

Refer to [this](./pipeline_configuration.md#defining-a-pipeline) for a detailed breakdown on pipeline configuration.

## Implementing a Node

A node requires:

* Inheriting the base node class **`aineko.core.node.AbstractNode`**
* Implementing at least the abstract method **`_execute`** and optionally **`_pre_loop_hook`** .

**`_pre_loop_hook` (optional)** is used to initialize the node's state before it starts to process data from the dataset.

**`_execute`** is the main logic that run recurrently. As of writing, user should explicitly produce and consume within this method like so:

```python
for dataset, consumer in self.consumers.items():
    # dataset is the name of the dataset as defined in the pipeline yml configuration
    # consumer is a DatasetConsumer object
    msg = consumer.consume(how="next")
```
