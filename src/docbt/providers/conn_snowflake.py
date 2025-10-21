"""Snowflake Connector Class"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

# Handle optional dependencies
try:
    import pandas as pd
    import snowflake.connector
    from snowflake.connector import DictCursor, SnowflakeConnection

    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    # Type checking imports to avoid errors in IDEs
    if TYPE_CHECKING:
        import pandas as pd
        import snowflake.connector
        from snowflake.connector import DictCursor, SnowflakeConnection


class ConnSnowflake:
    """A connector class to run SQL commands against Snowflake.

    Supports multiple authentication methods:
    1. Username/password authentication
    2. Key pair authentication (private key)
    3. SSO/OAuth authentication
    4. Environment variables (fallback)
    """

    def __init__(
        self,
        account: str | None = None,
        user: str | None = None,
        password: str | None = None,
        warehouse: str | None = None,
        database: str | None = None,
        schema: str | None = None,
        role: str | None = None,
        private_key: bytes | None = None,
        private_key_path: str | None = None,
        authenticator: str | None = None,
        **kwargs,
    ):
        """
        Initialize Snowflake connector.

        Example usage - Option 1: Using environment variables from .env
        Make sure SNOWFLAKE_* variables are set in your .env file
        conn = ConnSnowflake()

        Example usage - Option 2: Using explicit credentials
        conn = ConnSnowflake(
            account='xy12345.us-east-1',
            user='your_username',
            password='your_password',
            warehouse='COMPUTE_WH',
            database='YOUR_DB',
            schema='PUBLIC',
            role='YOUR_ROLE'
        )

        Example usage - Option 3: Using SSO/Browser authentication
        conn = ConnSnowflake(
            account='xy12345.us-east-1',
            user='your_username',
            authenticator='externalbrowser',
            warehouse='COMPUTE_WH',
            database='YOUR_DB',
            schema='PUBLIC'
        )

        Example usage - Option 4: Using key pair authentication
        conn = ConnSnowflake(
            account='xy12345.us-east-1',
            user='your_username',
            private_key_path='/path/to/rsa_key.p8',
            warehouse='COMPUTE_WH',
            database='YOUR_DB',
            schema='PUBLIC'
        )


        Args:
            account: Snowflake account identifier (e.g., 'xy12345.us-east-1')
            user: Username for authentication
            password: Password for authentication
            warehouse: Default warehouse to use
            database: Default database to use
            schema: Default schema to use
            role: Default role to use
            private_key: Private key bytes for key pair authentication
            private_key_path: Path to private key file for key pair authentication
            authenticator: Authentication method ('snowflake', 'externalbrowser', 'oauth', etc.)
            **kwargs: Additional connection parameters passed to snowflake.connector.connect()

        Raises:
            ImportError: If snowflake-connector-python is not installed
        """
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError(
                "Snowflake connector is not installed. "
                "Install it with: pip install docbt[snowflake]"
            )

        self.account = account or os.getenv("DOCBT_SNOWFLAKE_ACCOUNT")
        self.user = user or os.getenv("DOCBT_SNOWFLAKE_USER")
        self.password = password or os.getenv("DOCBT_SNOWFLAKE_PASSWORD")
        self.warehouse = warehouse or os.getenv("DOCBT_SNOWFLAKE_WAREHOUSE")
        self.database = database or os.getenv("DOCBT_SNOWFLAKE_DATABASE")
        self.schema = schema or os.getenv("DOCBT_SNOWFLAKE_SCHEMA")
        self.role = role or os.getenv("DOCBT_SNOWFLAKE_ROLE")
        self.authenticator = authenticator or os.getenv("DOCBT_SNOWFLAKE_AUTHENTICATOR")
        self.private_key = private_key or os.getenv("DOCBT_SNOWFLAKE_PRIVATE_KEY")
        self.private_key_path = private_key_path or os.getenv("DOCBT_SNOWFLAKE_PRIVATE_KEY_PATH")
        self.extra_params = kwargs
        self.connection = self._create_connection()

    def _load_private_key(self) -> bytes | None:
        """Load private key from file if path is provided."""
        if self.private_key:
            return self.private_key

        if self.private_key_path:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization

            with open(self.private_key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,  # Add password parameter if key is encrypted
                    backend=default_backend(),
                )

            return private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

        return None

    def _create_connection(self) -> SnowflakeConnection:
        """Create and return a Snowflake connection."""
        conn_params = {
            "account": self.account,
            "user": self.user,
        }

        # Add optional parameters if provided
        if self.warehouse:
            conn_params["warehouse"] = self.warehouse
        if self.database:
            conn_params["database"] = self.database
        if self.schema:
            conn_params["schema"] = self.schema
        if self.role:
            conn_params["role"] = self.role

        # Handle authentication methods
        if self.authenticator:
            conn_params["authenticator"] = self.authenticator

        if self.private_key or self.private_key_path:
            conn_params["private_key"] = self._load_private_key()

        if self.password:
            conn_params["password"] = self.password

        # Add any extra parameters
        conn_params.update(self.extra_params)

        return snowflake.connector.connect(**conn_params)

    def execute_query(
        self, query: str, params: tuple | None = None, use_dict_cursor: bool = False
    ) -> Any:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string to execute
            params: Optional tuple of parameters for parameterized queries
            use_dict_cursor: If True, return results as dictionaries

        Returns:
            Cursor with query results
        """
        if use_dict_cursor:
            cursor = self.connection.cursor(DictCursor)
        else:
            cursor = self.connection.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        return cursor

    def query_data(
        self, query: str, params: tuple | None = None, dataframe: bool = True
    ) -> list[dict[str, Any]] | pd.DataFrame:
        """
        Execute a SQL query and return results as a list of dictionaries.

        Args:
            query: SQL query string to execute
            params: Optional tuple of parameters for parameterized queries
            dataframe: If True, return results as a pandas DataFrame

        Returns:
            List of dictionaries representing rows
        """
        cursor = self.execute_query(query, params, use_dict_cursor=True)
        results = cursor.fetchall()
        if dataframe:
            results = pd.DataFrame(results)
        cursor.close()
        return results

    def execute_dml(self, query: str, params: tuple | None = None) -> int:
        """
        Execute a DML statement (INSERT, UPDATE, DELETE) and return affected rows.

        Args:
            query: DML query string to execute
            params: Optional tuple of parameters for parameterized queries

        Returns:
            Number of affected rows
        """
        cursor = self.execute_query(query, params)
        rowcount = cursor.rowcount
        cursor.close()
        self.connection.commit()
        return rowcount

    def execute_ddl(self, query: str, params: tuple | None = None) -> bool:
        """
        Execute a DDL statement (CREATE, ALTER, DROP).

        Args:
            query: DDL query string to execute
            params: Optional tuple of parameters for parameterized queries

        Returns:
            True if successful
        """
        cursor = self.execute_query(query, params)
        cursor.close()
        return True

    def execute_many(self, query: str, data: list[tuple]) -> int:
        """
        Execute a query multiple times with different parameter sets.

        Args:
            query: SQL query string with placeholders
            data: List of parameter tuples

        Returns:
            Total number of affected rows
        """
        cursor = self.connection.cursor()
        cursor.executemany(query, data)
        rowcount = cursor.rowcount
        cursor.close()
        self.connection.commit()
        return rowcount

    def table_exists(
        self, table_name: str, database: str | None = None, schema: str | None = None
    ) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Name of the table
            database: Database name (uses default if not provided)
            schema: Schema name (uses default if not provided)

        Returns:
            True if table exists, False otherwise
        """
        db = database or self.database
        sch = schema or self.schema

        query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_catalog = %s
            AND table_schema = %s
            AND table_name = %s
        """

        try:
            cursor = self.execute_query(query, (db.upper(), sch.upper(), table_name.upper()))
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0
        except Exception:
            return False

    def get_table_schema(
        self, table_name: str, database: str | None = None, schema: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get the schema of a table.

        Args:
            table_name: Name of the table
            database: Database name (uses default if not provided)
            schema: Schema name (uses default if not provided)

        Returns:
            List of dictionaries with column information
        """
        db = database or self.database
        sch = schema or self.schema

        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_catalog = %s
            AND table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position
        """

        return self.execute_query_to_list(query, (db.upper(), sch.upper(), table_name.upper()))

    def list_databases(self) -> list[str]:
        """
        List all databases accessible to the user.

        Returns:
            List of database names
        """
        query = "SHOW DATABASES"
        cursor = self.execute_query(query, use_dict_cursor=True)
        databases = [row["name"] for row in cursor.fetchall()]
        cursor.close()
        return databases

    def list_schemas(self, database: str | None = None) -> list[str]:
        """
        List all schemas in a database.

        Args:
            database: Database name (uses default if not provided)

        Returns:
            List of schema names
        """
        db = database or self.database
        query = f"SHOW SCHEMAS IN DATABASE {db}"
        cursor = self.execute_query(query, use_dict_cursor=True)
        schemas = [row["name"] for row in cursor.fetchall()]
        cursor.close()
        return schemas

    def list_tables(self, database: str | None = None, schema: str | None = None) -> list[str]:
        """
        List all tables in a schema.

        Args:
            database: Database name (uses default if not provided)
            schema: Schema name (uses default if not provided)

        Returns:
            List of table names
        """
        db = database or self.database
        sch = schema or self.schema
        query = f"SHOW TABLES IN {db}.{sch}"
        cursor = self.execute_query(query, use_dict_cursor=True)
        tables = [row["name"] for row in cursor.fetchall()]
        cursor.close()
        return tables

    def use_warehouse(self, warehouse: str):
        """Set the active warehouse."""
        self.execute_query(f"USE WAREHOUSE {warehouse}")
        self.warehouse = warehouse

    def use_database(self, database: str):
        """Set the active database."""
        self.execute_query(f"USE DATABASE {database}")
        self.database = database

    def use_schema(self, schema: str):
        """Set the active schema."""
        self.execute_query(f"USE SCHEMA {schema}")
        self.schema = schema

    def use_role(self, role: str):
        """Set the active role."""
        self.execute_query(f"USE ROLE {role}")
        self.role = role

    def commit(self):
        """Commit the current transaction."""
        self.connection.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.connection.rollback()

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise e

    def close(self):
        """Close the Snowflake connection."""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
