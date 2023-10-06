---
description: Pipeline, Node, Datasets
---

# Concepts

## What is an Aineko Pipeline?

In day-to-day conversations, the term _pipeline_ frequently denotes either a Pipeline name, Pipeline definition or a Pipeline execution. Aineko documentation aims to differentiate them explicitly.&#x20;

An Aineko pipeline is a streaming workflow. This means that data is continuously being transmitted and sent over to different components in a way that allows for real-time processing of the data.&#x20;

In a pipeline, you may implement arbitrary computation units, (**Nodes**) and specify where they consume data from, and where they send that data to. (**Datasets**) An Aineko Pipeline allows you to construct complex processing graphs that processes streaming data.&#x20;

### Pipeline Definition&#x20;

A pipeline definition is a specialised Program that we write - to tell us what a pipeline comprises.&#x20;



### An aineko pipeline is made up of **Dataset(s)** and **Node(s).**&#x20;

&#x20;\
A Dataset is an abstraction for a buffer for data that we can define producers and consumers for. Producers write data to a dataset, while consumers read data from the dataset. It is analogous to a **pub-sub topic or channel**. In the current version of aineko, it is a **Kafka Topic,** but in future, other implementations of message channels could be pluggable too.&#x20;

A **Node** is an abstraction for some computation, a function if you will. At the same time a **Node** can be a producer and/or a consumer of a **Dataset**.

This means that we created three datasets - **test\_sequence,** **test\_sum** and **logging**. logging is a default dataset we create for all aineko pipelines to log messages to.&#x20;

We also created two nodes - `sum` and `sequence`&#x20;

The output of sequence **`node`** feeds into **`sum`** via **`test_sequence`**, which passes the data to **`test_sum`**
