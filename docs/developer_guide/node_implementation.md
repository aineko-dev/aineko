# Building a Node

Nodes are essentially units of compute that encapsulate any event-driven logic you can define in python. Whether it is a transformation, an API call or a data transfer, as long as you can express it in python, it can be contained in a node!

## Implementing a Node

To illustrate how a node should be constructed, we will go through an example of a simple node that consumes a number from an input dataset, increments it by 1, then produces it to an output dataset.

```python title="sum_node.py"
from aineko.internals.node import AbstractNode

class MySumNode(AbstractNode):

    def _pre_loop_hook(self, params=None):
        """Optional; used to initialize node state."""
        self.state = params.get("initial_state", 0)

    def _execute(self, params=None):
        """Required; function repeatedly executes."""
        msg = self.consumers["test_sequence"].next()
        self.log(
            f"Received input: {msg['message']}. Adding {params['increment']}..."
        )
        self.state = int(msg["message"]) + int(params["increment"])
        self.producers["test_sum"].produce(self.state)
```

### `_pre_loop_hook`

You can optionally define a `_pre_loop_hook` method in your node class to intialize the state of your node with class variables. If the `node_params` key is defined in `pipeline.yml`, it will be passed in under the `params` argument.

```python title="sum_node.py" hl_lines="5-7"
from aineko.internals.node import AbstractNode

class MySumNode(AbstractNode):

    def _pre_loop_hook(self, params=None):
        """Optional; used to initialize node state."""
        self.state = params.get("initial_state", 0)

    def _execute(self, params=None):
        """Required; function repeatedly executes."""
        msg = self.consumers["test_sequence"].next()
        self.log(
            f"Received input: {msg['message']}. Adding {params['increment']}..."
        )
        self.state = int(msg["message"]) + int(params["increment"])
        self.producers["test_sum"].produce(self.state)
```

### `_execute`

The `_execute` method is repeatedly executed as the pipeline runs. We recommend nodes to follow a design pattern of constantly polling for new data and taking action when new data is received.

```python title="sum_node.py" hl_lines="9-16"
from aineko.internals.node import AbstractNode

class MySumNode(AbstractNode):

    def _pre_loop_hook(self, params=None):
        """Optional; used to initialize node state."""
        self.state = params.get("initial_state", 0)

    def _execute(self, params=None):
        """Required; function repeatedly executes."""
        msg = self.consumers["test_sequence"].next()
        self.log(
            f"Received input: {msg['message']}. Adding {params['increment']}..."
        )
        self.state = int(msg["message"]) + int(params["increment"])
        self.producers["test_sum"].produce(self.state)
```

The only way to an node "dies", or when the `_execute` loop terminates, is when the entire pipeline goes down or when the [poison pill](#poison-pill) is activated. 


### Producers & Consumers

Node classes inherit attributes named `self.producers` and `self.consumers` that are each a dictionary, keyed by dataset name with values being `DatasetProducer` and `DatasetConsumer` objects respectively. These objects allow you to produce/consume data to/from a dataset from your catalog config.

```python title="sum_node.py" hl_lines="11 16"
from aineko.internals.node import AbstractNode

class MySumNode(AbstractNode):

    def _pre_loop_hook(self, params=None):
        """Optional; used to initialize node state."""
        self.state = params.get("initial_state", 0)

    def _execute(self, params=None):
        """Required; function repeatedly executes."""
        msg = self.consumers["test_sequence"].next()
        self.log(
            f"Received input: {msg['message']}. Adding {params['increment']}..."
        )
        self.state = int(msg["message"]) + int(params["increment"])
        self.producers["test_sum"].produce(self.state)
```

!!! warning "Producers and Consumers must be included in the pipeline configuration"
    They must be defined in the `outputs` and `inputs` list respectively to be available to the node. If a dataset is not available in a Node's catalog, a `KeyError` will be raised.

A node can produce to a dataset, consume from a dataset, or both. Nodes that consume are triggered to action by the arrival of new data in the dataset they consume from.

!!! info "Examples on possible ways to connect nodes with datasets"

    === "Produce only"

        This node only produces to two datasets, and acts like a source for datasets:

        ```mermaid
        flowchart LR
        classDef datasetClass fill:#87CEEB
        classDef nodeClass fill:#eba487
        N_node_producer_only((node_producer_only)):::nodeClass -->  T_produced_dataset_1[produced_dataset_1]:::datasetClass
        N_node_producer_only((node_producer_only)):::nodeClass -->  T_produced_dataset_2[produced_dataset_2]:::datasetClass
        ```

    === "Consume only"

        This node only consumes from two datasets, and acts like a sink for datasets:
        ```mermaid
        flowchart LR
        classDef datasetClass fill:#87CEEB
        classDef nodeClass fill:#eba487
        T_consumed_dataset_1[consumed_dataset_1]:::datasetClass -->  N_node_consumer_only((node_consumer_only)):::nodeClass
        T_consumed_dataset_2[consumed_dataset_2]:::datasetClass -->  N_node_consumer_only((node_consumer_only)):::nodeClass
        ```

    === "Consume and Produce"

        A node that both consumes and produces datasets acts like a transformer for datasets. The consumed datasets are the inputs to the transformer, and the produced datasets are the outputs of the transformer:
        ```mermaid
        flowchart LR
        classDef datasetClass fill:#87CEEB
        classDef nodeClass fill:#eba487
        T_consumed_dataset[consumed_dataset]:::datasetClass -->  N_node_transformer((node_transformer)):::nodeClass
        N_node_transformer((node_transformer)):::nodeClass -->  T_produced_dataset[produced_dataset]:::datasetClass
        ```

### Logging

Node classes inherit a method named `self.log` that allows users to log messages. You can set the appropriate level from: `info`, `debug`, `warning`, `error`, an `critical`. You can log from inside of the `_pre_loop_hook` method, the `_execute` method, or any other method you add to your node.

:   
    ```python
    self.log(f"Produced {self.cur_integer}", level="info")
    ```


### Poison Pill

Poison pills refers to an "emergency shut down" button that can be triggered in times of emergency. Every node has access to a `activate_poison_pill` method that will terminate the entire pipeline and kill all nodes. To invoke it, use the following syntax.

:   
    ```python
    node.activate_poison_pill()
    ```