# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Example file showing unit testing."""

from {{cookiecutter.project_slug}}.nodes import MySumNode


def test_mynode():
    """Unit test for MySumNode."""

    mynode = MySumNode(
        node_name="MySumNode",
        pipeline_name="test_pipeline",
        test=True
    )
    inputs = [{"value": 1}, {"value": 2}, {"value": 3}]
    mynode.setup_test(
        inputs={
            "test_sequence": inputs,
        },  # input a list of elements to be consumed
        outputs=["test_sum"],  # list of dataset names that are produced to
        params={"initial_state": 0, "increment": 1},
    )
    outputs = mynode.run_test()
    for produced_message, input_values in zip(outputs["test_sum"], inputs):
        assert produced_message["value"] == input_values["value"] + 1

    assert mynode.state == 4
