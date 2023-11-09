---
description: Pipeline, Node, Datasets
---

# Concepts

??? info "What is an Aineko Pipeline?"

    In day-to-day conversations, the term _pipeline_ frequently denotes either a Pipeline definition or a Pipeline execution. Aineko documentation aims to differentiate them explicitly.

    An Aineko pipeline is a streaming workflow. This means that data is continuously being transmitted and sent over to different components in a way that allows for real-time processing of the data.

    In a pipeline, you may implement arbitrary computation units (**Nodes**), and specify where they consume data from, and where they send that data to (**Datasets**). An Aineko Pipeline allows you to construct complex processing graphs that processes streaming data.

## Pipeline Definition

A pipeline definition is a specialised Program that we write - to tell us what a pipeline comprises. A Pipeline definition is defined in yaml and essentially allows us to compose computation nodes together by specifying the input and output buffers that they consume data from and produce data to.

See [here](./pipeline_configuration.md) to learn about writing a pipeline definition.

## Pipeline Execution

If a pipeline definition is a program, then a pipeline execution is a process. You can run multiple pipeline executions for a single pipeline definition.

## Dataset

A Dataset is an abstraction for a buffer for data that we can define producers and consumers for. Producers write data to a dataset, while consumers read data from the dataset. It is analogous to a **pub-sub topic or channel**. In the current version of aineko, it is a **Kafka Topic,** but in future, other implementations of message channels could be pluggable too.

## Node

A **Node** is an abstraction for some computation, a function if you will. At the same time a **Node** can be a producer and/or a consumer of a **Dataset**.

A node can optionally consume from topics, process that data and produce the output to another buffer that we can chain other Node consumers on.
