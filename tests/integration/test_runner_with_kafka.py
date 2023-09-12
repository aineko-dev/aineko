"""Tests that runner is able to generate a pipeline that works
with a kafka service running in the background.
"""

from aineko.core.node import AbstractNode
from aineko.core.runner import Runner
from aineko.core.dataset import DatasetConsumer

import ray
from typing import Optional
import time

class Counter(AbstractNode):
    """Node that counts integers every second."""
    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        self.limit = 10
        self.counter = 0

    def _execute(self, params: Optional[dict] = None) -> None:
        """Counts integers every second."""
        if self.counter < self.limit:
            self.producers["count"].produce(self.counter)
            self.counter += 1
            time.sleep(0.2)
        else:
            self.producers["count"].produce("END")
            return False
        
    def _post_loop_hook(self, params: Optional[dict] = None) -> None:
        time.sleep(2)
        self.activate_poison_pill()
        print("Poison pill activated")

def test_integation_pipeline():
    runner = Runner(
        project = "integration_test",
        pipeline = "integration_test",
        conf_source = "tests/integration/conf"
    )
    try:
        runner.run()
    except ray.exceptions.RayActorError:
        consumer = DatasetConsumer(
            dataset_name = "count",
            node_name = "consumer",
            pipeline_name="integration_test",
        )
        count_messages = consumer.consume_all(end_message="END")
        count_values = [msg["message"] for msg in count_messages]
        assert count_values == list(range(10))
