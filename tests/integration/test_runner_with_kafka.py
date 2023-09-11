"""Tests that runner is able to generate a pipeline that works
with a kafka service running in the background.
"""

from aineko.core.node import AbstractNode
from aineko.core.runner import Runner

from typing import Optional
import time

class Counter(AbstractNode):
    """Node that counts integers every second."""

    def _execute(self, params: Optional[dict] = None):
        """Counts integers every second."""
        i = 0
        while True:
            self.producers["count"].produce(i)
            i += 1
            print(i)
            time.sleep(1)

def test_integation_pipeline():
    runner = Runner(
        project = "integration_test",
        pipeline = "integration_test",
        conf_source = "tests/integration/conf"
    )
    runner.run()
