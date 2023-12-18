---
hide:
  - toc
  - path
---

# Welcome to Aineko

Aineko simplifies the developer experience, and helps team create fast and reliable intelligent applications by abstracting away the complexities of deployment.

## What is Aineko?

Aineko is a python framework for building powerful data applications quickly. You can use it to simplify development in many ways, including build your back-end and data stacks, process streaming data, or manage generative AI feedback loops.

<div class="grid cards" markdown>

- __Code Faster__ <br><br> Use pre-built nodes that work with popular data sources like REST APIs
- __Always Robust__ <br><br> Production-ready from the get-go. Scale with ease.
- __Stateful Computation__ <br><br> Aineko supports long-running stateful computations.
- __Composable__ <br><br> Scale your project easily with engineering best practices.
- __Fast__ <br><br> Achieve microsecond latency between nodes.*
- __Scalable__ <br><br> Process billions or records per day with ease.*

</div>

\* As measured from an internal use case. Performance may vary depending on exact use case.

## How to Get Started?

As an open source framework, you can install and build pipelines on your local machines. You can explore how easy it is to go from idea to pipeline, see its scale and modularity, and see how fast it processes real-time data. 

To unlock the true power of the framework, try [Aineko Cloud](https://cloud-docs.aineko.dev). Aineko Cloud  simplifies your tooling by bundling tedious infrastructure, helping you scale, automate deployment, and collaborate as a team. 


### Aineko Products

<div class="grid cards" markdown>

-   __Open Source Framework__

    ___

    Prototype locally, and discover:

    - How quickly idea to pipeline takes
    - Scale and modularity
    - Real-time data processing

    [Quickstart Guide](./start/quickstart.md){ .md-button .md-button--primary }

-   __Aineko Cloud__

    ___

    Upgrade to unlock the full power of Aineko:

    - Run your pipelines in the cloud
    - Share projects & collaborate
    - Automated infrastructure deployments

    [Demo Cloud](https://cloud-docs.aineko.dev){ .md-button .md-button--primary }

</div>

## Developer Guide

<div class="grid" markdown>

<div markdown>
### Core Concepts

- [Pipeline](./developer_guide/concepts.md#pipeline-definition)
- [Node](./developer_guide/concepts.md#node)
- [Dataset](./developer_guide/concepts.md#dataset)
- [Workflow](./developer_guide/concepts.md#workflow)
- [Aineko Cloud](https://cloud-docs.aineko.dev/){:target="_blank"}
</div>

<div markdown>
### Creating & Building Pipelines

1. [Create an Aineko Project](./developer_guide/aineko_project.md)
2. [Pipeline Configuration](./developer_guide/pipeline_configuration.md)
3. [Building a Node](./developer_guide/node_implementation.md)
4. [CLI Documentation](./developer_guide/cli.md)
5. [Configuring Kafka](./developer_guide/config_kafka.md)

</div>
</div>

---

## Extras

Supercharge your development by using pre-built nodes directly in your pipeline. Aineko extras contains nodes that are production-ready out of the box.

- [FastAPI node](./extras/fastapi.md)

---

## API Documentation

- [`AbstractNode`](./api_reference/abstract_node.md)
- [`DatasetConsumer`](./api_reference/dataset_consumer.md)
- [`DatasetProducer`](./api_reference/dataset_producer.md)
- [Pipeline `Config`](./api_reference/config.md)
- [`ConfigLoader`](./api_reference/config_loader.md)
- [`Runner`](./api_reference/runner.md)

---

## Examples & Templates

### Common use cases

<div class="grid cards" markdown>

-   __Self-checking AI Agents__

    ___

    Create an AI agent that accepts user prompts, iterates on an answer, and outputs it only after all specified checks pass.

    [:octicons-arrow-right-24: Aineko Dream](./examples/aineko_dream)


</div>


## Join the Community

Have questions or "ah-ha" moments? Building something cool with Aineko? Go ahead and share it with the Aineko community.

[:fontawesome-brands-slack: Join our Slack](https://join.slack.com/t/aineko-dev/shared_invite/zt-27z2vi9k7-OvTeysc2yIPVrF4Yqo5qzw){ .md-button }

[Contribution Guide](./community){ .md-button .md-button--primary }
