# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Dataset to connect to PostgreSQL databases."""
import os
from typing import Dict, Optional, Union

import boto3
from mypy_boto3_rds import RDSClient
from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from aineko.core.dataset import AsyncAbstractDataset, DatasetError


class AWSDatasetHelper:
    """Utility class for connecting to datasets on AWS."""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        """Initialize the AWSDatasetHelper.

        The values for the AWS credentials and region name can be
        provided as arguments to the constructor. If not provided,
        the values will be read from the following environment variables:

            - AWS_ACCESS_KEY_ID
            - AWS_SECRET_ACCESS_KEY
            - AWS_REGION

        Args:
            aws_access_key_id: AWS access key ID.
            aws_secret_access_key: AWS secret access key.
            region_name: AWS region name.
        """
        self.aws_access_key_id = aws_access_key_id or os.environ.get(
            "AWS_ACCESS_KEY_ID"
        )
        self.aws_secret_access_key = aws_secret_access_key or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.region_name = region_name or os.environ.get("AWS_DEFAULT_REGION")

    def get_rds_endpoint(self, db_instance_identifier: str) -> str:
        """Get the RDS endpoint for a given RDS instance.

        Args:
            db_instance_identifier: RDS instance identifier.
        """
        rds_client: RDSClient = boto3.client(
            "rds",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )
        db_instances = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_identifier
        )
        db_instance = db_instances["DBInstances"][0]
        return db_instance["Endpoint"]["Address"]


class Postgres(AsyncAbstractDataset):
    """Dataset to connect to a table in a PostgreSQL database."""

    def __init__(
        self,
        name: str,
        host: str,
        dbname: str,
        user: str,
        password: str,
    ):
        self.name = name
        self.host = host
        self.dbname = dbname
        self.user = user
        self.password = password

        self._pool = None

    async def connect(self):
        """Connect to the PostgreSQL database."""
        self._pool = AsyncConnectionPool(
            f"dbname={self.dbname} user={self.user} password={self.password}"
            f" host={self.host}",
            open=False,
        )
        await self._pool.open()

    async def create(
        self,
        schema: Dict[str, str],
        extra_commands: str = "",
    ):
        """Create a new postgres table.

        Executes the SQL command:

            ```SQL
            CREATE TABLE table_name (column_name column_type, ...)
            ```

        Extra SQL commands can be supplied and will be added to
        the back.

        Args:
            schema: mapping between column name and column
                type. Type must be a valid SQL type.
            extra_commands: extra SQL commands to be added
                to the table creation query.
        """
        query = sql.SQL(
            "CREATE TABLE {name} ({schema}) {extra_commands};"
        ).format(
            name=sql.Identifier(self.name),
            schema=sql.SQL(
                (",").join([f"{key} {value}" for key, value in schema.items()])
            ),
            extra_commands=sql.SQL(extra_commands),
        )
        await self.execute_query(query)

    async def read(self, query):
        raise NotImplementedError("Not yet implemented.")

    #     # await self.execute_query
    #     await self.acur.execute(query)
    #     return self.acur.fetchall()

    async def write(self, query):
        raise NotImplementedError("Not yet implemented.")

    #     await self.acur.execute(query)
    #     await self.aconn.commit()

    async def delete(self, if_exists: bool = False):
        """Drops the table from the Postgres database.

        Args:
            if_exists: If table does not exist, do not raise error.
                Defaults to False.
        """
        if if_exists:
            query = "DROP TABLE IF EXISTS {name};"
        else:
            query = "DROP TABLE {name};"

        await self.execute_query(
            sql.SQL(query).format(name=sql.Identifier(self.name)),
        )

    async def exists(self):
        """Queries the database to check if the table exists."""
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT EXISTS(
                        SELECT FROM information_schema.tables
                        WHERE table_name = %(name)s);
                    """,
                    {"name": self.name},
                )
                result = await cur.fetchone()
                return result[0]

    async def execute_query(self, query: Union[str, sql.SQL], *args, **kwargs):
        """Handles execution of PostgreSQL queries.

        Args:
            query: SQL query to execute.
            args: Arguments to pass to the query.
            kwargs: Keyword arguments to pass to the query.
        """
        if args and kwargs:
            raise DatasetError("Please use only args or kwargs, not both.")
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
                    if args:
                        await cur.execute(query, args)
                    else:
                        await cur.execute(query, kwargs)
                    await conn.commit()  # TODO check if we want autocommit or not

                except Exception as exc:
                    await conn.rollback()
                    raise DatasetError(
                        f"Failed to execute query: {query}"
                    ) from exc

    async def close(self):
        """Close the connection to the PostgreSQL database."""
        if self._pool.closed is False:
            await self._pool.close()
            print(f"closed {self._pool.closed}")
