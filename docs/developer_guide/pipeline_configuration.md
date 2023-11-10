# Building a Pipeline

At a high-level, building a pipeline requires defining a pipeline and implementing at least a node.

## Defining a pipeline

```mermaid
flowchart LR
classDef datasetClass fill:#87CEEB
classDef nodeClass fill:#eba487
N_sequence((sequence)):::nodeClass -->  T_test_sequence[test_sequence]:::datasetClass
```
For the sake of simplicity, we reference a truncated version of the pipeline definition below:

???+ example "Example `pipeline.yml` configuration file"
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

A pipeline definition should have the following attributes:

## Keys

### `pipeline`

This is the top-level key in a pipeline configuration file, a configuration map to define the name, default settings, nodes, and datasets for a pipeline.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `name` | Y | string | Name of the pipeline. |
| `default_node_settings` | N | map | Defines common default values for node attributes which can be overridden at the node level. |
| `nodes` | Y | map | Defines the compute nodes for a pipeline, mapping to node names. |
| `datasets` | Y | map | Defines the compute nodes for a pipeline, mapping to structs with node name keys. |


#### `default_node_settings`

This optional section can be used to set common default settings for all nodes in the pipeline. These settings can be overridden at the node level. Currently, the main setting that can be set here is the number of CPUs allocated to a node, `num_cpus`.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `num_cpus` | N | float | Defines default number of CPUs for a node. Can be less than one. |

#### `nodes`

This section defines the compute nodes for a pipeline.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `<name of node>` | Y | map | Defines map of node names to node structures in the pipeline. |

##### `<name of node>`

A particular node instance in the pipeline, defined by a unique name. Each node is defined by a class, inputs, outputs, node parameters, and num_cpus. Any parameters defined at the individual node level will locally overwrite any default settings defined at the `default_node_settings` level.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `class` | Y | string | Defines which python class to run for node. |
| `inputs` | N | list of strings | Defines which datasets to consume from if applicable. |
| `outputs` | N | list of strings | Defines which datasets to produce to if applicable. |
| `node_params` | N | map | Defines any arbitrary params relevant for node's application logic. In the example above, we defined `initial_state` and `increment` params, which are both integers.|
| `num_cpus` | Y | float | Number of CPUs allocated to a node. Required either for each node definition or at default_node_settings level.|



#### `datasets`

This section defines the datasets for a pipeline.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `<name of dataset>` | Y | map | Defines map of dataset names to dataset structures in the pipeline. |

##### `<name of dataset>`

A particular dataset instance in the pipeline, defined by a unique name. Each dataset is defined by a type.

| Key | Required | Type | Description |
| --- | -------- | ---- | ----------- |
| `type` | Y | string | Defines which type of dataset to use. Currently, only `kafka_stream` is supported. |

!!! note
    Aineko is currently in the Beta release stage and is constantly improving.

    If you have any feedback, questions, or suggestions, please [reach out](mailto:support@aineko.dev) to us.
