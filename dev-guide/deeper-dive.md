---
description: A closer look into how a pipeline is defined and some CLI commands
---

# Deeper dive

This is a continuation of the [previous section (Quick Start)](http://127.0.0.1:5000/o/ShdDMx0cKFmhzyW8MlIt/s/vWEVF5jYXkgdTAeQH5nC/). Before starting, make sure you have already created a template project using `aineko create`.&#x20;

### Directory contents

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

This is how the boilerplate directory look - many of these files are boilerplate files to make things work.&#x20;

Let's zoom in on the more interesting files to take note of:&#x20;

1. **`conf/pipeline.yml`** - This contains your pipeline definition that you are expected to modify to define your own pipeline. It is defined in yaml.&#x20;
2. **`my_awesome_pipeline/nodes.py`** - Remember how nodes are abstractions for computations? These nodes are implemented in Python. You do not have to strictly define them in this file. You can define them anywhere you like within the directory as long as you reference them correctly in `pipeline.yml`.&#x20;
3. **`docker-compose.yml`** - When we invoke `aineko run` , datasets has to be initialised - which means that we need to create Kafka topics. This file contains the image we need to create containers from, as well as other configurations like env var and network settings. _You typically do not have to change this file._&#x20;

### Defining a Pipeline &#x20;

For the sake of simplicity, we reference a truncated version of the pipeline below:&#x20;

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

A pipeline should have the following attributes:&#x20;

* **`name`** - name of the pipeline&#x20;
* **`default_node_settings`**&#x20;
  * **`num_cpus` -**  Number of cpus allocated to a node&#x20;
* **`nodes`**&#x20;
  * **\<name of node>**&#x20;
    * **`class`** - which python class to run&#x20;
    * **`inputs` -** which dataset to consume from if applicable
    * **`outputs`** - which dataset to produce to if applicable&#x20;
    * **`node_params`** - define any arbitrary params relevant for node's application logic&#x20;
* **datasets**
  * **\<name\_of\_dataset>**&#x20;
    * **type** - only `kafka_stream` is supported right now, which maps to a kafka topic&#x20;

### Implementing a Node

To implement a node, the key is to inherit **`aineko.core.node.AbstractNode`** and implement two key abstract methods **`_pre_loop_hook`** and **`_execute`**.&#x20;

**`_pre_loop_hook` (optional)** is used to initialize the node's state before it starts to process data from the dataset.&#x20;

**`_execute`** is the main logic that run recurrently. As of writing, user should explicitly produce and consume within this method like so:&#x20;

```python
for dataset, consumer in self.consumers.items():
    msg = consumer.consume(how="next")

```
