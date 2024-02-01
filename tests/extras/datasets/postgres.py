# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for Postgres dataset."""

import pytest

from aineko.extras import AWSDatasetHelper, Postgres


class TestAWSDatasetHelper:
    """Tests for AWSDatasetHelper."""

    def test_get_rds_endpoint(self):
        """Test get_rds_endpoint."""
        helper = AWSDatasetHelper()
        endpoint = helper.get_rds_endpoint("shawn-dataset")
        assert isinstance(endpoint, str)


@pytest.fixture(scope="module")
def postgres_table():
    """Create a postgres table for testing."""
    dataset = Postgres(
        name="test_table",
        host="shawn-dataset.ch4nbfnhdik6.us-east-1.rds.amazonaws.com",
        dbname="postgres_db",
        user="postgres",
        password="testpassword",
    )
    yield dataset
    # dataset.delete(if_exists=True)


class TestPostgres:
    """Tests for Postgres dataset."""

    def test_create(self, postgres_table):
        """Test create."""
        postgres_table.create(
            schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"},
        )
        assert postgres_table.exists()

    def test_delete(self, postgres_table):
        """Test delete."""
        postgres_table.delete()
        assert not postgres_table.exists()
