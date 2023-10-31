---
description: Fastest way to get an Aineko pipeline up and running
---

# Quick Start

### Technical Dependencies&#x20;

1. [Docker](https://www.docker.com/get-started/)&#x20;
2. [Poetry](https://python-poetry.org/docs/#installation) (a python dependency manager)&#x20;
3. [Python](https://www.python.org/downloads/) (version 3.10)&#x20;

### Steps

**Step 1: Install Aineko**&#x20;

Install virtual environment. Optional step, but a best practice to isolate dependencies installed.&#x20;

```
python -m venv venv
source venv/bin/activate
pip install aineko
```

**Step 2: Create a template pipeline with aineko cli**&#x20;

```
aineko create
```

You will see the following prompts as `aineko` tries to create a project directory containing the boilerplate you need for a pipeline. Feel free to use the defaults suggested! &#x20;

```
  [1/5] project_name (My Awesome Pipeline):
  [2/5] project_slug (my_awesome_pipeline):
  [3/5] project_description (Behold my awesome pipeline!):
  [4/5] authors (John Doe <johndoe@gmail.com>):
  [5/5] pipeline_slug (test-aineko-pipeline):
```

**Step 3: Install dependencies in the new pipeline**&#x20;

```
cd my_awesome_pipeline
poetry install
```

**Step 4: Start the Aineko background services**

```
aineko service start --file docker-compose.yml
```

**Step 5: Start the template pipeline**&#x20;

```sh
aineko run ./conf/pipeline.yml
```

You will see the following output:&#x20;

```
Creating dataset: test_sequence: {'type': 'kafka_stream'}
Creating dataset: test_sum: {'type': 'kafka_stream'}
Creating dataset: logging: {'type': 'kafka_stream', 'params': {'num_partitions': 1, 'replication_factor': 1, 'config': {'retention.ms': 604800000}}}
All datasets created.
2023-10-06 00:01:15,122 INFO worker.py:1633 -- Started a local Ray instance. View the dashboard at 127.0.0.1:8266 
Running sequence node on my_awesome_pipeline pipeline: inputs=None, outputs=['test_sequence', 'logging']
Running sum node on my_awesome_pipeline pipeline: inputs=['test_sequence'], outputs=['test_sum', 'logging']
Running node_manager node on my_awesome_pipeline pipeline: inputs=None, outputs=['logging']
```

**So that's it to get an Aineko pipeline running! We hope that was smooth for you!**&#x20;

{% hint style="info" %}
**What does the above output mean?**&#x20;

An aineko pipeline is made up of **Dataset(s)** and **Node(s).**  \
A Dataset can be thought of as a mailbox. Nodes pass messages to this mailbox, that can be read by many other Nodes.&#x20;

A **Node** is an abstraction for some computation, a function if you will. At the same time a **Node** can be a producer and/or a consumer of a **Dataset**. (mailbox)&#x20;

The output means that we have successfully created three datasets - **test\_sequence,** **test\_sum** and **logging and** two nodes - **sum** and **sequence**.
{% endhint %}

To learn more about Pipeline, Datasets and Nodes, you can visit this page. &#x20;

So below is the pipeline we just ran, using the aineko cli, you can also see this pipeline rendered in the browser:&#x20;

```sh
aineko visualize --browser ./conf/pipeline.yml
```

<figure><img src="../.gitbook/assets/image.png" alt=""><figcaption><p>The pipeline we just ran </p></figcaption></figure>



