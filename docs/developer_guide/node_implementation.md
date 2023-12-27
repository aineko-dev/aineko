# Building a node

Nodes are essentially units of compute that encapsulate any event-driven logic you can define in python. Whether it's a transformation, an API call or a data transfer, as long as you can express it in python, it can be contained in a node.

## Implementing a node

To illustrate how a node should be constructed, we will go through an example of a simple node that consumes a number from an input dataset, increments it by 1, then produces it to an output dataset.

```python title="sum_node.py"
from aineko.core.node import AbstractNode

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

You can optionally define a `_pre_loop_hook` method in your node class to initialize the state of your node with class variables. If the `node_params` key is defined in `pipeline.yml`, it will be passed in under the `params` argument.

```python title="sum_node.py" hl_lines="5-7"
from aineko.core.node import AbstractNode

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
from aineko.core.node import AbstractNode

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

A node will only terminate when the entire pipeline goes down or when the [poison pill](#poison-pill) is activated. 


### Producers & consumers

Node classes inherit attributes named `self.producers` and `self.consumers` that are each a dictionary, with keys being the dataset name and values being `DatasetProducer` and `DatasetConsumer` objects respectively. These objects allow you to produce/consume data to/from a dataset.

This is an example of typical usage within a node:

```python title="sum_node.py" hl_lines="11 16"
from aineko.core.node import AbstractNode

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
        
#### Consume Methods

Depending on the architecture of the node, there are several methods of consuming from a consumer. The available methods are listed below.

The most common case is to wait till a new message arrives, then consume it immediately. The best way to do this is:
:   
    ```python title="Waiting for the next available message"
    self.consumers["dataset"].next()
    ```

In some cases, data is being produced faster than it can be consumed, and we just want the freshest, most recent message each time. To do this:

:   
    ```python title="Getting the most recent message"
    self.consumers["dataset"].last(timeout=1)
    ```

In cases where you might require more low-level control over consumption patterns, such as consuming from multiple datasets in the same node, the low-level `consume` method can be used.

:   
    ```python title="More fine-tune control"
    self.consumers["dataset"].consume(how="next", timeout=1)
    ```

The timeout argument in these methods signify the duration in which the method has to return a message otherwise it will re-poll for a new one.


### Logging
#### From within a node
Node classes inherit a method named `self.log` that allows users to produce messages to the `logging` dataset. This is useful for debugging and monitoring purposes. You can specify the level of the log message, by specifying the `level` argument. By default, the level is set to `info`. Other valid levels are `debug`, `warning`, `error`, and `critical`. You can log from any method that inherits from `AbstractNode`.

:   
    ```python
    self.log(f"Produced {self.cur_integer}", level="info")
    ```

#### From outside a node
Since `self.log` is inherited from `AbstractNode`, you can't use it outside of a node. However, you can still log to the `logging` dataset by using the native Python `logging` module and specifying the `logging_namespace` and setting `log_to_dataset` to `true` in the node or pipeline configuration as shown below. This configuration will read all log entries from the "foo" namespace and produce them to the `logging` dataset.

:   

    ```yaml title="conf/pipeline.yml" linenums="7"
    nodes:
      example_node:
        class: your_package.your_module.YourNode
        log_to_dataset: true
        logging_namespace: foo
    ```

    ```python title="your_package/your_utils.py" linenums="7"
    import logging

    logger = logging.getLogger("foo")
    
    def some_function():
        logger.info("Hello world!")
    ```
 
    ```python title="your_package/your_module.py"
    from your_package.your_utils import some_function
    from aineko.core.node import AbstractNode

    class YourNode(AbstractNode):
        def _execute(self, params=None):
            some_function()
    ```
??? note
    * In the preceding example, the `logging_namespace` is set to `foo`. This means that only log entries with the namespace "foo" will be read and produced to the `logging` dataset. If you want to read and produce all log entries, set `logging_namespace` to `None`.
    * Since nodes are isolated processes, the preceding example will only read logs that are written when invoked (either directly or indirectly) by the node. Specifying the logging parameters at the node level allows for very fine-grained control over what log messages are read and produced. However, the same parameters can be specified at the pipeline level. This will read all log entries from the specified namespace and produce them to the `logging` dataset.

    :   
        ```yaml title="conf/pipeline.yml" linenums="7"
        nodes:
          example_node:
            class: your_package.your_module.YourNode
          second_node:
            class: your_package.your_module.YourSecondNode        
           
        log_to_dataset: true
        logging_namespace: foo
        ```


### PoisonPill

Poison pills refers to an "emergency shut down" button that can be triggered in times of emergency. Every node has access to a `activate_poison_pill` method that will terminate the entire pipeline and kill all nodes. To invoke it, use the following syntax.

:   
    ```python
    node.activate_poison_pill()
    ```
