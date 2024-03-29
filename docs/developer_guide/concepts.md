---
description: Pipeline, Node, Datasets
---

# Concepts

??? info "What is an Aineko Pipeline?"

    In day-to-day conversations, the term _pipeline_ frequently denotes either a Pipeline definition or a Pipeline execution. Aineko documentation aims to differentiate them explicitly.

    An Aineko pipeline is a streaming workflow. This means that data is continuously being transmitted and sent over to different components in a way that allows for real-time processing of the data.

    In a pipeline, you may implement arbitrary computation units (**Nodes**), and specify where they read data from, and where they send that data to (**Datasets**). An Aineko Pipeline allows you to construct complex processing graphs that processes streaming data.

## Pipeline definition

A pipeline definition is a specialised Program that you write - to tell Aineko what a pipeline comprises. A Pipeline definition is defined in YAML and essentially allows Aineko to compose computation nodes together by specifying the input and output buffers that they read data from and write data to.

See [here](./pipeline_configuration.md) to learn about writing a pipeline definition.

## Pipeline execution

If a pipeline definition is a program, then a pipeline execution is a process. You can run multiple pipeline executions for a single pipeline definition.

## Dataset

A Dataset is an abstraction for a buffer for data that you can define inputs and outputs for. Outputs write data to a dataset, while inputs read data from the dataset. It's analogous to a **pub-sub topic or channel**. In the current version of aineko, it's a **Kafka Topic,** but in future, other implementations of message channels could be pluggable too.

## Node

A **Node** is an abstraction for some computation, akin to a function. At the same time a **Node** can be a writer and/or a reader of a **Dataset**.

A node can optionally read from topics, process that data and write the output to another buffer that you can chain other Node readers on.

## Workflow

A **workflow** is a series of steps that occur as part of the CI/CD process. For example, a **continuous integration workflow** contains steps that checks the validity of your deployment configuration. A **continuous deployment workflow**, on the other hand, orchestrates the necessary changes in the cloud to deploy the most recent version of your code.