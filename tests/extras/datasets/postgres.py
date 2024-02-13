# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for Postgres dataset."""
# pylint: disable=redefined-outer-name
from contextlib import asynccontextmanager

import pytest

from aineko.extras import AsyncPostgresDataset, AWSDatasetHelper


class TestAWSDatasetHelper:
    """Tests for AWSDatasetHelper."""

    def test_get_rds_endpoint(self):
        """Test get_rds_endpoint."""
        helper = AWSDatasetHelper()
        endpoint = helper.get_rds_endpoint("shawn-dataset")
        assert isinstance(endpoint, str)


@pytest.fixture
def postgres_db() -> AsyncPostgresDataset:
    """Create an instance of the Postgres dataset with predefined parameters."""
    dataset = AsyncPostgresDataset(
        name="test_table",
        host="shawn-dataset.ch4nbfnhdik6.us-east-1.rds.amazonaws.com",
        dbname="postgres_db",
        user="postgres",
        password="testpassword",
    )
    return dataset


@pytest.fixture
@asynccontextmanager
async def pg_session_with_table(postgres_db: AsyncPostgresDataset):
    """Create a connected instance of the Postgres dataset with a test table.

    This fixture creates a connected instance of the AsyncPostgresDataset with
    a test table. The table is deleted after the test is run.

    Yields:
        A connected instance of the AsyncPostgresDataset with a test table.

    """
    async with postgres_db as dataset:
        if await dataset.exists() is False:
            await dataset.create(
                schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"}
            )
            yield dataset
        else:
            yield dataset
        await dataset.delete(if_exists=True)


@pytest.fixture
@asynccontextmanager
async def pg_session_without_table(postgres_db: AsyncPostgresDataset):
    """Create a connected instance of the Postgres dataset without a test table.

    This fixture creates a connected instance of the AsyncPostgresDataset and
    deletes the test table if it exists.

    Yields:
        A connected instance of the AsyncPostgresDataset without a test table.
    """
    async with postgres_db as dataset:
        await dataset.delete(if_exists=True)
        yield dataset


class TestPostgres:
    """Tests for Postgres dataset."""

    @pytest.mark.asyncio
    async def test_create(
        self, pg_session_without_table, postgres_db: AsyncPostgresDataset
    ):
        """Test the create method."""
        async with pg_session_without_table as dataset:
            await dataset.create(
                schema={"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(255)"},
            )
            assert await postgres_db.exists()

    @pytest.mark.asyncio
    async def test_delete(self, pg_session_with_table: AsyncPostgresDataset):
        """Test the delete method."""
        async with pg_session_with_table as dataset:
            assert await dataset.exists() is True
            await dataset.delete(if_exists=True)
            assert await dataset.exists() is False

    @pytest.mark.asyncio
    async def test_exists(self, pg_session_with_table: AsyncPostgresDataset):
        """Test the exists method."""
        async with pg_session_with_table as dataset:
            assert await dataset.exists() is True
