# Aineko CLI

The Aineko CLI is a dev tool that allows you to get started quickly and introspect your pipeline runs more expediently.&#x20;

## Commands supported&#x20;

**`aineko create`**&#x20;

Creates a template pipeline project that you can go into, poetry install and start a pipeline with `aineko run`&#x20;

**`aineko run <path/to/pipeline/definition/config> [--pipeline-name=<pipeline-name>] [--retry]`**

Creates all the datasets by starting the kafka topic, and uses Ray to run all the nodes.&#x20;

**`aineko service [start | stop | restart]`**

Starts up, shuts down and restart the Kafka service and Kafka topics. This also includes the creation and destruction of the Dataset. (Kafka Topic)&#x20;

**`aineko stream -d <dataset> [--from-start]`**

View all the logs produced to the dataset since it was first created

**`aineko visualize <path/to/pipeline/definition/config> [-b/ --browser]`**

Visualize the Aineko Pipeline that you have defined.&#x20;
