# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ainode.core.node module."""
import time

import pytest

from aineko.core.node import AbstractNode

NUM_MESSAGES = 10


def test_node_setup_and_run_test(dummy_node) -> None:
    """Tests the setup_test and run_test methods."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    node = dummy_node(node_name, pipeline_name, test=True, poison_pill=None)
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

    node_name = "test"
    pipeline_name = "testing_pipeline"

    sequencer = test_sequencer_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    sequencer.setup_test(
        inputs=None,
        outputs=["integer_sequence"],
        params={"sleep_time": 0.1, "num_messages": NUM_MESSAGES},
    )
    outputs = sequencer.run_test()
    assert outputs["integer_sequence"] == list(range(NUM_MESSAGES))

    doubler = test_doubler_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    doubler.setup_test(
        inputs={"integer_sequence": list(range(NUM_MESSAGES))},
        outputs=["integer_doubles"],
    )
    outputs = doubler.run_test()
    assert outputs["integer_doubles"] == [i * 2 for i in range(NUM_MESSAGES)]


def test_output_yielding(test_sequencer_node, test_doubler_node) -> None:
    """Test sequencer & doubler nodes, focusing on the output per iteration."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    sequencer: AbstractNode = test_sequencer_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    sequencer.setup_test(
        inputs=None,
        outputs=["integer_sequence"],
        params={"sleep_time": 0.1, "num_messages": NUM_MESSAGES},
    )

    for _, output, node_instance in sequencer.run_test_yield():
        assert output["integer_sequence"] == node_instance.cur_integer - 1

    doubler: AbstractNode = test_doubler_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )
    doubler.setup_test(
        inputs={"integer_sequence": list(range(NUM_MESSAGES))},
        outputs=["integer_doubles"],
    )
    for _, output, node_instance in doubler.run_test_yield():
        assert output["integer_doubles"] == node_instance.cur_integer * 2


def test_output_yielding_no_output(test_internal_value_setter_node):
    """Test internal value setter node, focusing on the node state per iteration."""
    node_name = "test"
    pipeline_name = "testing_pipeline"

    node: AbstractNode = test_internal_value_setter_node(
        node_name, pipeline_name, test=True, poison_pill=None
    )

    input_sequence = list(range(NUM_MESSAGES))
    node.setup_test(inputs={"integer_sequence": input_sequence}, outputs=[])
    for input, _, node_instance in node.run_test_yield():
        if input.get("integer_sequence"):
            assert input["integer_sequence"] == node_instance.cur_integer + 1


@pytest.mark.parametrize("test_log_internals", [None], indirect=True)
def test_root_logger(test_log_internals):
    """Test that the root logger is used when no namespace is provided."""
    node: tuple(AbstractNode, int) = test_log_internals[0](
        node_name="test",
        pipeline_name="testing_pipeline",
        log_to_dataset=True,
        logging_namespace=None,
    )
    node.enable_test_mode()
    node.setup_test(inputs=None, outputs=["logging", "messages"])
    outputs = node.run_test()

    for log_entry in outputs["logging"]:
        assert "Dummy function called." in log_entry["log"]

    assert len(outputs["logging"]) == test_log_internals[1]


@pytest.mark.parametrize("test_log_internals", ["hello"], indirect=True)
def test_namespaced_logger(test_log_internals, subtests):
    """Test that the namespaced logger is used when a namespace is provided."""
    with subtests.test("Test with matching namespace"):
        node: AbstractNode = test_log_internals[0](
            node_name="test",
            pipeline_name="testing_pipeline",
            log_to_dataset=True,
            logging_namespace="hello",
        )
        node.enable_test_mode()
        node.setup_test(inputs=None, outputs=["logging", "messages"])
        outputs = node.run_test()

        for log_entry in outputs["logging"]:
            assert "Dummy function called." in log_entry["log"]

        assert len(outputs["logging"]) == test_log_internals[1]

    with subtests.test("Test with non-matching namespace"):
        node: AbstractNode = test_log_internals[0](
            node_name="test",
            pipeline_name="testing_pipeline",
            log_to_dataset=True,
            logging_namespace="goodbye",
        )
        node.enable_test_mode()
        node.setup_test(inputs=None, outputs=["logging", "messages"])
        outputs = node.run_test()

        assert len(outputs["logging"]) == 0
