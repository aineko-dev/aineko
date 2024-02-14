---
description: A closer look into how a pipeline is defined and some CLI commands
---

# Aineko project

!!! note
    This is a continuation of the [previous section (Quick Start)](../start/quickstart.md). Before starting, make sure you have already created a template project using `aineko create`.

## Directory contents

```
.
├── README.md
├── conf
│   └── pipeline.yml
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

1. **`conf/pipeline.yml`** - This contains your pipeline definition that you are expected to modify to define your own pipeline. It is defined in YAML.
2. **`my_awesome_pipeline/nodes.py`** - Remember how nodes are abstractions for computations? These nodes are implemented in Python. You do not have to strictly define them in this file. You can define them anywhere you like within the directory as long as you reference them correctly in `pipeline.yml`.

## Defining a pipeline

Pipelines are defined using a `.yml` file that contains specific keys. In this configuration file, you can assemble a pipeline from nodes and datasets.

Refer to [this](./pipeline_configuration.md#defining-a-pipeline) for a detailed breakdown on pipeline configuration.

## Implementing a node

A node requires:

* Inheriting the base node class **`aineko.core.node.AbstractNode`**
* Implementing at least the abstract method **`_execute`** and optionally **`_pre_loop_hook`** .

**`_pre_loop_hook` (optional)** is used to initialize the node's state before it starts to process data from the dataset.

**`_execute`** is the main logic that run recurrently. As of writing, user should explicitly read and write within this method like so:

```python
def _execute(self, params: Optional[dict] = None):
    """This node takes an input number and increments it by 1."""
    input_number = self.inputs["my_input_dataset"].next()
    # if we want the most recent message, we can use .last()
    output_number = input_number + 1
    self.outputs["my_output_dataset"].write(output_number)
    
```
