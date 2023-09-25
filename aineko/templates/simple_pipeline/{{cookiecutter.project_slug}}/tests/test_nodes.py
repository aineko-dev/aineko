"""Example file showing unit testing."""

from lib.nodes import MySumNode


def test_mynode():
    """Unit test for MySumNode."""

    mynode = MySumNode(test=True)
    mynode.setup_test(
        inputs={
            "test_sequence": [1, 2, 3]
        },  # input a list of elements to be consumed
        outputs=["test_sum"],  # list of dataset names that are produced to
        params={"initial_state": 0, "increment": 1},
    )
    outputs = mynode.run_test()
    assert outputs["test_sum"] == [2, 3, 4]
    assert mynode.state == 4
