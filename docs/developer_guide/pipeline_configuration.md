# Building a Pipeline

At a high-level, building a pipeline requires defining a pipeline and implementing at least a node.

## Defining a pipeline

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
  * **`num_cpus` -**  Number of cpus allocated to a node
* **`nodes`**
  * **<name of node\>**
    * **`class`** - which python class to run
    * **`inputs` -** which dataset to consume from if applicable
    * **`outputs`** - which dataset to produce to if applicable
    * **`node_params`** - define any arbitrary params relevant for node's application logic
* **datasets**
  * **<name\_of\_dataset\>**
    * **type** - only `kafka_stream` is supported right now, which maps to a kafka topic

!!! note
    Aineko is currently in the Beta release stage and is constantly improving.

    If you have any feedback, questions, or suggestions, please [reach out](mailto:support@aineko.dev) to us.
