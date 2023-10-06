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

### Pipeline.yml&#x20;





