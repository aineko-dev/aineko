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
def postgres_table() -> Postgres:
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

    @pytest.mark.asyncio
    async def test_create(self, postgres_table: Postgres):
        """Test create."""
        await postgres_table.connect()

        await postgres_table.create(
            schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"},
        )
        assert await postgres_table.exists()

    @pytest.mark.asyncio
    async def test_delete(self, postgres_table: Postgres):
        """Test delete."""
        await postgres_table.connect()

        await postgres_table.delete()
        assert await postgres_table.exists() is False

    @pytest.mark.asyncio
    async def test_exists(self, postgres_table: Postgres):
        """Test exists."""
        await postgres_table.connect()

        await postgres_table.create(
            schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"},
        )
        assert await postgres_table.exists() is True

        # assert await postgres_table.exists() is False
        # await postgres_table.create(
        #     schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"},
        # )
        # assert await postgres_table.exists() is True
        # await postgres_table.delete()
        # assert await postgres_table.exists() is False
        # print("Table created")
