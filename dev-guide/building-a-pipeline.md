# Building a Pipeline

On a high-level, building a pipeline requires a pipeline definition and node's implementation.&#x20;

## Implementing a Node&#x20;

```
from aineko.config import AINEKO_CONFIG
from aineko.internals.node import AbstractNode

class TestSequencer(AbstractNode):
    """Test sequencer node."""
    ...
```

**Pre-Loop Hook**

You can optionally define a `_pre_loop_hook` method in your node class to intialize the state of your node with class variables. The `_pre_loop_hook` method consumes params that are provided in the pipeline configuration, so you can define the initial state of your node via your pipeline config.

```
def _pre_loop_hook(self, params: dict = None):
    """Pre loop hook."""
    self.cur_integer = int(params.get("start_int", 0))
    self.num_messages = 0
```

**Execute Method**

The `_execute` method of the node is wrapped by the `execute` method in the `AbstractNode` base class. The `_execute` method is called constantly in a while loop. The loop only terminates based on the strategy provided to the `NodeManager` (executes as an infinite loop by default) or by the user returning False from the `_execute` method. Nodes work best when they are constantly polling for new data from consumers or from outside systems and taking actions depending on the data that is consumed.

```
def _execute(self, params: dict = None):
    """Generates a sequence of integers and writes them to a dataset.
    Args:
        params: Parameters for the node
    Returns:
        None
    """
    # Break if duration has been exceeded
    if self.num_messages >= params.get("num_messages", 25):
        return False
    ...
```

**Producers & Consumers**

Node classes inherit attributes named `self.producers` and `self.consumers` that are each a dictionary, keyed by dataset name with values being `DatasetProducer` and `DatasetConsumer` objects, respectively. These objects allow you to produce/consume data to/from a dataset from your catalog config.

```
def _execute(self, params: dict = None):
    """Generates a sequence of integers and writes them to a dataset.
    Args:
        params: Parameters for the node
    Returns:
        None
    """
    # Break if duration has been exceeded
    if self.num_messages >= params.get("num_messages", 25):
        return False

    # Write message to producer
    self.producers["integer_sequence"].produce(self.cur_integer)
    self.log(f"Produced {self.cur_integer}", level="info")
    self.num_messages += 1

    # Increment integer and sleep
    self.cur_integer += 1
    time.sleep(params.get("sleep_time", 1))
```

The producers and consumers you use in your node must be made available to your node via the pipeline configuration. If a dataset is not available in a Node's catalog, a `KeyError` will be raised.

**Logging**

Node classes inherit a method named `self.log` that allows users to log messages to Amber, where logs are aggregated and triaged across observability pipelines. You can set the appropriate level from: `info`, `debug`, `warning`, `error`, an `critical`.

```
self.log(f"Produced {self.cur_integer}", level="info")
```

You can log from inside of the `_pre_loop_hook` method, the `_execute` method, or any other method you add to your node.\


## Defining a pipeline&#x20;

For the sake of simplicity, we reference a truncated version of the pipeline below:&#x20;

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

A pipeline should have the following attributes:&#x20;

* **`name`** - name of the pipeline&#x20;
* **`default_node_settings`**&#x20;
  * **`num_cpus` -**  Number of cpus allocated to a node&#x20;
* **`nodes`**&#x20;
  * **\<name of node>**&#x20;
    * **`class`** - which python class to run&#x20;
    * **`inputs` -** which dataset to consume from if applicable
    * **`outputs`** - which dataset to produce to if applicable&#x20;
    * **`node_params`** - define any arbitrary params relevant for node's application logic&#x20;
* **datasets**
  * **\<name\_of\_dataset>**&#x20;
    * **type** - only `kafka_stream` is supported right now, which maps to a kafka topic&#x20;

###

\


{% hint style="info" %}
Aineko is currently in the Alpha release stage and is constantly improving.&#x20;

If you have any feedback, questions, or suggestions, please [reach out](mailto:support@convexlabs.xyz) to us.
{% endhint %}
