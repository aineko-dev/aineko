# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Example file showing unit testing."""

from {{cookiecutter.project_slug}}.nodes import MySumNode


def test_mynode(message_helper):
    """Unit test for MySumNode."""

    mynode = MySumNode(
        node_name="MySumNode",
        pipeline_name="test_pipeline",
        test=True
    )
    mynode.setup_test(
        dataset_type="aineko.datasets.kafka.KafkaDataset", # The dataset type to use
        inputs={
            "test_sequence": [1, 2, 3]
        },  # input a list of elements to be read
        outputs=["test_sum"],  # list of dataset names that are written to
        params={"initial_state": 0, "increment": 1},
    )
    outputs = mynode.run_test()
    assert message_helper(outputs["test_sum"]) == [2, 3, 4]
    assert mynode.state == 4
