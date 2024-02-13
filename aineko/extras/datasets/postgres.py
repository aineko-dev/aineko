# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Dataset to connect to PostgreSQL databases."""
import os
from types import TracebackType
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

import boto3
from mypy_boto3_rds import RDSClient
from psycopg import AsyncCursor, errors, rows, sql
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


class AsyncPostgresDataset(AsyncAbstractDataset):
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

        self._pool: AsyncConnectionPool

    async def __aenter__(self) -> "AsyncPostgresDataset":
        self._pool = AsyncConnectionPool(
            f"dbname={self.dbname} user={self.user} password={self.password}"
            f" host={self.host}",
            open=False,
        )
        await self._pool.open()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        if self._pool.closed is False:
            await self._pool.close()

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

    async def read(self, query: Union[str, sql.SQL, sql.Composed]) -> List[Any]:
        """Performs a read operation on the Postgres database.

        Args:
            query: SQL query to execute.

        Returns:
            A list of rows returned by the query.
        """
        cursor = await self.execute_query(query=query)
        return await cursor.fetchall()

    async def write(
        self,
        query: Union[str, sql.SQL, sql.Composed],
        parameters: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
    ) -> Optional[List]:
        """Performs a write operation on the Postgres database.

        Args:
            query: SQL query to execute.
            parameters: Parameters to be passed to the query. Defaults to None.

        Returns:
            A list of rows returned by the query if the query produced results.
            None otherwise.
        """
        cursor = await self.execute_query(query, parameters=parameters)
        try:
            return await cursor.fetchall()
        except errors.ProgrammingError as e:
            if "the last operation didn't produce a result" in str(e):
                return None
            raise e

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

    async def exists(self) -> bool:
        """Queries the database to check if the table exists."""
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query="""
                    SELECT EXISTS(
                        SELECT FROM information_schema.tables
                        WHERE table_name = %(name)s);
                    """,
                    params={"name": self.name},
                )
                result: Tuple[bool, None] = await cur.fetchone()
                return result[0]

    async def execute_query(
        self,
        query: Union[str, sql.SQL, sql.Composed],
        parameters: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
    ) -> AsyncCursor[rows.TupleRow]:
        """Handles execution of PostgreSQL queries.

        Args:
            query: SQL query to execute.
            parameters: Parameters to be passed to the query. Defaults to None.

        Returns:
            AsyncCursor: Cursor object for the executed query. Can be used to
                         fetch results.

        Raises:
            DatasetError: If the query execution fails for any reason.
        """
        async with self._pool.connection() as conn:
            try:
                cursor: AsyncCursor = await conn.execute(
                    query=query, params=parameters
                )
                await conn.commit()
                return cursor

            except Exception as exc:
                await conn.rollback()
                raise DatasetError(f"Failed to execute query: {query}") from exc
