# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Dataset to connect to PostgreSQL databases."""

import os
from typing import Optional

import boto3
import psycopg2
from botocore.config import Config
from psycopg2 import sql

from aineko.datasets.core import AbstractDataset, DatasetError


class AWSDatasetHelper:
    """Utility class containing utility methods for connecting to datasets on AWS."""

    def __init__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        region_name: str = None,
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

    def get_rds_endpoint(self, db_instance_identifier: str):
        """Get the RDS endpoint for a given RDS instance.

        Args:
            db_instance_identifier: RDS instance identifier.
        """
        rds_client = boto3.client(
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


class Postgres(AbstractDataset):
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

        self.conn = None
        self.cursor = None

    def _create(
        self,
        schema: dict[str, str],
        extra_commands: Optional[str] = "",
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
            schema=sql.SQL((",").join([f"{k} {v}" for k, v in schema.items()])),
            extra_commands=sql.SQL(extra_commands),
        )
        self.execute_query(query)

    def _read(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _write(self, query):
        self.cursor.execute(query)
        self.conn.commit()

    def _delete(self, if_exists: bool = False):
        """Drops the table from the Postgres database.

        Args:
            if_exists: If table does not exist, do not raise error.
                Defaults to False.
        """
        if if_exists:
            query = "DROP TABLE IF EXISTS {name};"
        else:
            query = "DROP TABLE {name};"

        self.execute_query(
            sql.SQL(query).format(name=sql.Identifier(self.name)),
        )

    def _describe(self):
        return "A PostgreSQL dataset."

    def _exists(self):
        """Queries the database to check if the table exists."""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %(name)s);
        """
        self.execute_query(query, name=self.name)
        return self.cursor.fetchone()[0]

    def connect(self):
        """Connect to the PostgreSQL database."""
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
        )
        self.cursor = self.conn.cursor()

    def execute_query(self, query: str | sql.SQL, *args, **kwargs):
        """Handles execution of PostgreSQL queries.

        Args:
            query: SQL query to execute.
            args: Arguments to pass to the query.
            kwargs: Keyword arguments to pass to the query.
        """
        if args and kwargs:
            raise DatasetError("Please use only args or kwargs, not both.")
        if not self.cursor:
            self.connect()
        try:
            if args:
                self.cursor.execute(query, args)
            else:
                self.cursor.execute(query, kwargs)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise DatasetError(f"Failed to execute query: {query}") from e

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
