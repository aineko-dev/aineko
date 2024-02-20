# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
from aineko.models import config_schema


def test_NodeSettings(subtests):
    """Tests for NodeSettings."""
    with subtests.test("Test with no parameters"):
        converted = config_schema.NodeSettings().model_dump(exclude_none=True)
        assert converted == {}

    with subtests.test("Test with num_cpus"):
        converted = config_schema.NodeSettings(num_cpus=1.0).model_dump(
            exclude_none=True
        )
        assert converted == {"num_cpus": 1.0}

    with subtests.test("Test with extra, undefined parameters"):
        converted = config_schema.NodeSettings(
            num_cpus=1.0, num_gpu=1.0, memory=1000 * 1024 * 1024
        ).model_dump(exclude_none=True)
        assert converted == {
            "num_cpus": 1.0,
            "num_gpu": 1.0,
            "memory": 1000 * 1024 * 1024,
        }
