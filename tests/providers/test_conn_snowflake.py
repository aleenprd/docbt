"""Tests for Snowflake connector (ConnSnowflake)."""

from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

# Skip all tests in this module if Snowflake dependencies are not installed
pytest.importorskip("snowflake.connector")
pytest.importorskip("docbt.providers.conn_snowflake")

from docbt.providers.conn_snowflake import ConnSnowflake  # noqa: E402


class TestConnSnowflakeInit:
    """Test ConnSnowflake initialization."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_init_with_explicit_credentials(self, mock_connect):
        """Test initialization with explicit credentials."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test_account",
            user="test_user",
            password="test_password",
            warehouse="test_warehouse",
            database="test_database",
            schema="test_schema",
            role="test_role",
        )

        assert conn.account == "test_account"
        assert conn.user == "test_user"
        assert conn.password == "test_password"
        assert conn.warehouse == "test_warehouse"
        assert conn.database == "test_database"
        assert conn.schema == "test_schema"
        assert conn.role == "test_role"
        assert conn.connection == mock_connection

        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["account"] == "test_account"
        assert call_kwargs["user"] == "test_user"
        assert call_kwargs["password"] == "test_password"
        assert call_kwargs["warehouse"] == "test_warehouse"

    @patch.dict(
        "os.environ",
        {
            "DOCBT_SNOWFLAKE_ACCOUNT": "env_account",
            "DOCBT_SNOWFLAKE_USER": "env_user",
            "DOCBT_SNOWFLAKE_PASSWORD": "env_password",
            "DOCBT_SNOWFLAKE_WAREHOUSE": "env_warehouse",
        },
    )
    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_init_with_environment_variables(self, mock_connect):
        """Test initialization with environment variables."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake()

        assert conn.account == "env_account"
        assert conn.user == "env_user"
        assert conn.password == "env_password"
        assert conn.warehouse == "env_warehouse"

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_init_with_sso_authenticator(self, mock_connect):
        """Test initialization with SSO/externalbrowser authenticator."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test_account",
            user="test_user",
            authenticator="externalbrowser",
            warehouse="test_warehouse",
        )

        assert conn.authenticator == "externalbrowser"
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["authenticator"] == "externalbrowser"

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_init_with_extra_params(self, mock_connect):
        """Test initialization with extra connection parameters."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        ConnSnowflake(
            account="test_account",
            user="test_user",
            password="test_password",
            session_parameters={"QUERY_TAG": "test_tag"},
        )

        call_kwargs = mock_connect.call_args[1]
        assert "session_parameters" in call_kwargs
        assert call_kwargs["session_parameters"]["QUERY_TAG"] == "test_tag"


class TestConnSnowflakePrivateKey:
    """Test private key authentication."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_key_data")
    @patch("docbt.providers.conn_snowflake.ConnSnowflake._load_private_key")
    def test_load_private_key_from_file(self, mock_load_key, mock_file, mock_connect):
        """Test loading private key from file."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        mock_load_key.return_value = b"serialized_key"

        conn = ConnSnowflake(
            account="test_account",
            user="test_user",
            private_key_path="/path/to/key.p8",
            warehouse="test_warehouse",
        )

        mock_connect.call_args[1]
        # Verify that private key was attempted to be loaded
        assert conn.private_key_path == "/path/to/key.p8"

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_init_with_private_key_bytes(self, mock_connect):
        """Test initialization with private key bytes."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        private_key_bytes = b"test_key_bytes"

        ConnSnowflake(
            account="test_account",
            user="test_user",
            private_key=private_key_bytes,
            warehouse="test_warehouse",
        )

        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["private_key"] == private_key_bytes


class TestConnSnowflakeExecuteQuery:
    """Test execute_query method."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_query_basic(self, mock_connect):
        """Test basic query execution."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        result = conn.execute_query("SELECT 1")

        assert result == mock_cursor
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_query_with_params(self, mock_connect):
        """Test query execution with parameters."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        params = ("value1", "value2")
        result = conn.execute_query(
            "SELECT * FROM table WHERE col1 = %s AND col2 = %s", params=params
        )

        assert result == mock_cursor
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM table WHERE col1 = %s AND col2 = %s", params
        )

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    @patch("docbt.providers.conn_snowflake.DictCursor")
    def test_execute_query_with_dict_cursor(self, mock_dict_cursor, mock_connect):
        """Test query execution with dictionary cursor."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.execute_query("SELECT 1", use_dict_cursor=True)

        mock_connection.cursor.assert_called_once_with(mock_dict_cursor)


class TestConnSnowflakeQueryData:
    """Test query_data method."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_query_data_returns_dataframe(self, mock_connect):
        """Test query_data returns DataFrame by default."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        result = conn.query_data("SELECT * FROM users")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["id", "name"]
        mock_cursor.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_query_data_returns_list_of_dicts(self, mock_connect):
        """Test query_data returns list of dicts when dataframe=False."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_cursor.fetchall.return_value = mock_data
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        result = conn.query_data("SELECT * FROM users", dataframe=False)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result == mock_data


class TestConnSnowflakeExecuteDML:
    """Test execute_dml method."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_dml_insert(self, mock_connect):
        """Test DML execution for INSERT statement."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        affected_rows = conn.execute_dml("INSERT INTO table VALUES (1, 'test')")

        assert affected_rows == 1
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_dml_update(self, mock_connect):
        """Test DML execution for UPDATE statement."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        affected_rows = conn.execute_dml("UPDATE table SET name = 'updated'")

        assert affected_rows == 5
        mock_connection.commit.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_dml_delete(self, mock_connect):
        """Test DML execution for DELETE statement."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        affected_rows = conn.execute_dml("DELETE FROM table WHERE id > 10")

        assert affected_rows == 3


class TestConnSnowflakeExecuteDDL:
    """Test execute_ddl method."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_ddl_create_table(self, mock_connect):
        """Test DDL execution for CREATE TABLE."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        result = conn.execute_ddl("CREATE TABLE test (id INT, name VARCHAR)")

        assert result is True
        mock_cursor.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_ddl_drop_table(self, mock_connect):
        """Test DDL execution for DROP TABLE."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        result = conn.execute_ddl("DROP TABLE test")

        assert result is True


class TestConnSnowflakeExecuteMany:
    """Test execute_many method."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_execute_many_multiple_inserts(self, mock_connect):
        """Test execute_many with multiple INSERT statements."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        data = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
        affected_rows = conn.execute_many("INSERT INTO users VALUES (%s, %s)", data)

        assert affected_rows == 3
        mock_cursor.executemany.assert_called_once_with("INSERT INTO users VALUES (%s, %s)", data)
        mock_connection.commit.assert_called_once()


class TestConnSnowflakeTableOperations:
    """Test table operation methods."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_table_exists_true(self, mock_connect):
        """Test table_exists returns True when table exists."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)  # COUNT(*) = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test", user="test", password="test", database="TEST_DB", schema="TEST_SCHEMA"
        )
        exists = conn.table_exists("MY_TABLE")

        assert exists is True
        mock_cursor.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_table_exists_false(self, mock_connect):
        """Test table_exists returns False when table doesn't exist."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (0,)  # COUNT(*) = 0
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test", user="test", password="test", database="TEST_DB", schema="TEST_SCHEMA"
        )
        exists = conn.table_exists("NONEXISTENT_TABLE")

        assert exists is False

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_table_exists_with_exception(self, mock_connect):
        """Test table_exists returns False on exception."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test", user="test", password="test", database="TEST_DB", schema="TEST_SCHEMA"
        )
        exists = conn.table_exists("MY_TABLE")

        assert exists is False


class TestConnSnowflakeListOperations:
    """Test list operation methods."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_list_databases(self, mock_connect):
        """Test list_databases returns database names."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"name": "DATABASE1"},
            {"name": "DATABASE2"},
            {"name": "DATABASE3"},
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        databases = conn.list_databases()

        assert databases == ["DATABASE1", "DATABASE2", "DATABASE3"]
        mock_cursor.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_list_schemas(self, mock_connect):
        """Test list_schemas returns schema names."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"name": "PUBLIC"},
            {"name": "INFORMATION_SCHEMA"},
            {"name": "CUSTOM_SCHEMA"},
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test", database="TEST_DB")
        schemas = conn.list_schemas()

        assert schemas == ["PUBLIC", "INFORMATION_SCHEMA", "CUSTOM_SCHEMA"]
        mock_cursor.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_list_tables(self, mock_connect):
        """Test list_tables returns table names."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {"name": "TABLE1"},
            {"name": "TABLE2"},
            {"name": "TABLE3"},
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(
            account="test", user="test", password="test", database="TEST_DB", schema="PUBLIC"
        )
        tables = conn.list_tables()

        assert tables == ["TABLE1", "TABLE2", "TABLE3"]
        mock_cursor.close.assert_called_once()


class TestConnSnowflakeUseStatements:
    """Test USE statement methods."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_use_warehouse(self, mock_connect):
        """Test use_warehouse sets active warehouse."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.use_warehouse("NEW_WAREHOUSE")

        assert conn.warehouse == "NEW_WAREHOUSE"
        mock_cursor.execute.assert_called_once_with("USE WAREHOUSE NEW_WAREHOUSE")

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_use_database(self, mock_connect):
        """Test use_database sets active database."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.use_database("NEW_DATABASE")

        assert conn.database == "NEW_DATABASE"
        mock_cursor.execute.assert_called_once_with("USE DATABASE NEW_DATABASE")

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_use_schema(self, mock_connect):
        """Test use_schema sets active schema."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.use_schema("NEW_SCHEMA")

        assert conn.schema == "NEW_SCHEMA"
        mock_cursor.execute.assert_called_once_with("USE SCHEMA NEW_SCHEMA")

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_use_role(self, mock_connect):
        """Test use_role sets active role."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.use_role("NEW_ROLE")

        assert conn.role == "NEW_ROLE"
        mock_cursor.execute.assert_called_once_with("USE ROLE NEW_ROLE")


class TestConnSnowflakeTransactions:
    """Test transaction management methods."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_commit(self, mock_connect):
        """Test commit method."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.commit()

        mock_connection.commit.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_rollback(self, mock_connect):
        """Test rollback method."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.rollback()

        mock_connection.rollback.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_transaction_context_manager_success(self, mock_connect):
        """Test transaction context manager commits on success."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")

        with conn.transaction():
            pass

        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_transaction_context_manager_exception(self, mock_connect):
        """Test transaction context manager rolls back on exception."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")

        with pytest.raises(ValueError):
            with conn.transaction():
                raise ValueError("Test error")

        mock_connection.rollback.assert_called_once()
        mock_connection.commit.assert_not_called()


class TestConnSnowflakeContextManager:
    """Test context manager functionality."""

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_context_manager_enter(self, mock_connect):
        """Test context manager __enter__ returns self."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        with conn as context:
            assert context is conn

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_context_manager_exit_calls_close(self, mock_connect):
        """Test context manager __exit__ calls close."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        with conn:
            pass

        mock_connection.close.assert_called_once()

    @patch("docbt.providers.conn_snowflake.snowflake.connector.connect")
    def test_close_method(self, mock_connect):
        """Test close method calls connection.close()."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection

        conn = ConnSnowflake(account="test", user="test", password="test")
        conn.close()

        mock_connection.close.assert_called_once()
