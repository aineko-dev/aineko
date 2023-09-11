# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ainode.core.node module."""
import time

NUM_MESSAGES = 10


def test_node_setup_and_run_test(dummy_node) -> None:
    """Tests the setup_test and run_test methods."""
    node = dummy_node(test=True)
    inputs = {"input": [1, 2, 3]}
    outputs = ["output"]
    node.setup_test(inputs=inputs, outputs=outputs)

    start_time = time.time()
    output = node.run_test(runtime=1)
    run_time = time.time() - start_time

    # Check that correct keys exist
    assert set(output.keys()) == set(["logging", "output"])
    # Check that correct messages are received
    assert [i["message"] for i in output["output"] if i] == [1, 2, 3]
    # Check that timeout worked as intended
    assert run_time - 1 < 0.01


# pylint: disable=no-member
def test_node_unit_test(test_sequencer_node, test_doubler_node) -> None:
    """Test sequencer and doubler nodes."""

    sequencer = test_sequencer_node(test=True)
    sequencer.setup_test(
        inputs=None,
        outputs=["integer_sequence"],
        params={"sleep_time": 0.1, "num_messages": NUM_MESSAGES},
    )
    outputs = sequencer.run_test()
    assert outputs["integer_sequence"] == list(range(NUM_MESSAGES))

    doubler = test_doubler_node(test=True)
    doubler.setup_test(
        inputs={"integer_sequence": list(range(NUM_MESSAGES))},
        outputs=["integer_doubles"],
    )
    outputs = doubler.run_test()
    assert outputs["integer_doubles"] == [i * 2 for i in range(NUM_MESSAGES)]
