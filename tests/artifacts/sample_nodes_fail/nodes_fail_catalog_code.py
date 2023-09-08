"""Contains generator and checker nodes for test project.

This module has a node that contains an extra producer dataset
compared with test_project catalog and is expected to fail a
validation check between catalog and code.
"""

import time
from typing import Optional

import ray

from aineko import AbstractNode
from aineko.config import AINEKO_CONFIG

TEST_INPUT = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


class TestSequencerPatch(AbstractNode):
    """Node to patch sequencer node, emits a message per second.

    Attributes:
        sequence (list): Sequence of integers to produce

    Methods:
        _pre_loop_hook: Saves sequence as state
        _execute: Generates a sequence of integers and writes them to a dataset
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Saves sequence as state.

        Args:
            params: Parameters for the node
        """
        self.sequence = TEST_INPUT.copy()

    # pylint: disable=unused-argument
    def _execute(self, params: Optional[dict] = None) -> None:
        """Generates a sequence of integers and writes them to a dataset.

        This node is meant to simulate a fake TestSequencer node.

        Args:
            params: Parameters for the node
        """
        if len(self.sequence) == 0:
            return False

        i = self.sequence.pop(0) * 2
        self.producers["integer_sequence"].produce(i)
        self.producers["an_extra_producer"].produce(i)
        self.log(f"Produced {i}", level="info")
        time.sleep(1)


class TestDoublerChecker(AbstractNode):
    """Node to check that the sequence of integers is correct.

    Attributes:
        start_time (float): Time at which the node started.
        expected_messages (list): List of expected messages.
    """

    def _pre_loop_hook(self, params: Optional[dict] = None) -> None:
        """Initializes state.

        Args:
            params: Parameters for the node.
        """
        self.start_time = time.time()
        self.expected_messages = [4 * i for i in TEST_INPUT]
        self.report(f"expected messages: {self.expected_messages}")

    # pylint: disable=unused-argument
    def _execute(self, params: Optional[dict] = None) -> bool:
        """Checks that the sequence of integers is correct.

        This node is meant to simulate a fake TestChecker node.

        Args:
            params: Parameters for the node

        Returns:
            Whether the node should continue running
        """
        if (time.time() - self.start_time) > 30:
            self.log("Checking timed out")
            return False
        if len(self.expected_messages) == 0:
            self.log("All messages received")
            self.report("Checker node completed successfully")
            return False

        # Read message from consumer
        message = self.consumers["integer_doubles"].consume(
            how="next", timeout=0
        )

        if message is None:
            return

        # Log error if message is not expected
        expected_message = self.expected_messages.pop(0)
        if message["message"] != expected_message:
            self.log(
                f"unexpected message: {message}; expected: {expected_message}"
            )
        else:
            self.log(f"received expected message: {message}")
