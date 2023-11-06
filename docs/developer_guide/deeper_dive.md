---
description: A closer look into how a pipeline is defined and some CLI commands
---

# Deeper dive

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

For the sake of simplicity, we reference a truncated version of the pipeline below:

```yaml
pipeline:
  name: test-aineko-pipeline

  default_node_settings:
    num_cpus: 0.5

  nodes:
    sequence:
      class: my_awesome_pipeline.nodes.MySequencerNode
      outputs:
        - test_sequence
      node_params:
        initial_state: 0
        increment: 1


  datasets:
    test_sequence:
      type: kafka_stream

```

A pipeline should have the following attributes:

* **`name`** - name of the pipeline
* **`default_node_settings`**
  * **`num_cpus`** - Number of cpus allocated to a node

* **`nodes`**
    * **<name of node\>**
        * **`class`** - which python class to run
        * **`inputs` -** which dataset to consume from if applicable
        * **`outputs`** - which dataset to produce to if applicable
        * **`node_params`** - define any arbitrary params relevant for node's application logic

* **datasets**
    * **<name\_of\_dataset\>**
        * **`type`** - only `kafka_stream` is supported right now, which maps to a kafka topic

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
