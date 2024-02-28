# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ainode.core.node module."""
import time

from aineko.core.node import AbstractNode

NUM_MESSAGES = 10


def test_node_setup_and_run_test(dummy_node, message_helper) -> None:
    """Tests the setup_test and run_test methods."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    node = dummy_node(node_name, pipeline_name, test=True, poison_pill=None)
    inputs = {"input": [1, 2, 3]}
    outputs = ["output"]
    node.setup_test(
        dataset_type="aineko.datasets.kafka.KafkaDataset",
        inputs=inputs,
        outputs=outputs,
    )

    start_time = time.time()
    output = node.run_test(runtime=1)
    run_time = time.time() - start_time

    # Check that correct keys exist
    assert set(output.keys()) == set(["logging", "output"])
    # Check that correct messages are received
    assert message_helper(output["output"]) == inputs["input"]

    # Check that timeout worked as intended
    assert run_time - 1 < 0.01


# pylint: disable=no-member
def test_node_unit_test(
    test_sequencer_node, test_doubler_node, subtests, message_helper
) -> None:
    """Test sequencer and doubler nodes."""

    node_name = "test"
    pipeline_name = "testing_pipeline"
    with subtests.test("Test Sequencer Node"):
        sequencer = test_sequencer_node(
            node_name, pipeline_name, test=True, poison_pill=None
        )
        sequencer.setup_test(
            dataset_type="aineko.datasets.kafka.KafkaDataset",
            inputs=None,
            outputs=["integer_sequence"],
            params={"sleep_time": 0.1, "num_messages": NUM_MESSAGES},
        )
        outputs = sequencer.run_test()
        assert message_helper(outputs["integer_sequence"]) == list(
            range(NUM_MESSAGES)
        )

    with subtests.test("Test Doubler Node"):
        doubler = test_doubler_node(
            node_name, pipeline_name, test=True, poison_pill=None
        )
        doubler.setup_test(
            dataset_type="aineko.datasets.kafka.KafkaDataset",
            inputs={"integer_sequence": list(range(NUM_MESSAGES))},
            outputs=["integer_doubles"],
        )
        outputs = doubler.run_test()
        print(outputs["integer_doubles"])
        # assert message_helper(outputs["integer_doubles"]) == [
        #     i * 2 for i in range(NUM_MESSAGES)
        # ]


def test_output_yielding(
    test_sequencer_node, test_doubler_node, message_helper
) -> None:
    """Test sequencer & doubler nodes, focusing on the output per iteration."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    sequencer: AbstractNode = test_sequencer_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    sequencer.setup_test(
        dataset_type="aineko.datasets.kafka.KafkaDataset",
        inputs=None,
        outputs=["integer_sequence"],
        params={"sleep_time": 0.1, "num_messages": NUM_MESSAGES},
    )

    for _, output, node_instance in sequencer.run_test_yield():
        assert (
            message_helper(output["integer_sequence"])
            == node_instance.cur_integer - 1
        )

    doubler: AbstractNode = test_doubler_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    doubler.setup_test(
        dataset_type="aineko.datasets.kafka.KafkaDataset",
        inputs={"integer_sequence": list(range(NUM_MESSAGES))},
        outputs=["integer_doubles"],
    )
    for _, output, node_instance in doubler.run_test_yield():
        assert (
            message_helper(output["integer_doubles"])
            == node_instance.cur_integer * 2
        )


def test_output_yielding_no_output(
    test_internal_value_setter_node, message_helper
):
    """Test internal value setter node, focusing on the node state per iteration."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    node: AbstractNode = test_internal_value_setter_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )

    input_sequence = list(range(NUM_MESSAGES))
    node.setup_test(
        dataset_type="aineko.datasets.kafka.KafkaDataset",
        inputs={"integer_sequence": input_sequence},
        outputs=[],
    )
    for input, _, node_instance in node.run_test_yield():
        if input.get("integer_sequence"):
            assert (
                message_helper(input["integer_sequence"])
                == node_instance.cur_integer
            )
