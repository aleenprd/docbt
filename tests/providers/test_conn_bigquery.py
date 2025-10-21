"""Tests for BigQuery connector (ConnBigQuery)."""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Skip all tests in this module if BigQuery dependencies are not installed
pytest.importorskip("google.cloud.bigquery")
pytest.importorskip("docbt.providers.conn_bigquery")

from google.cloud import bigquery  # noqa: E402

from docbt.providers.conn_bigquery import ConnBigQuery  # noqa: E402


class TestConnBigQueryInit:
    """Test ConnBigQuery initialization."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_init_with_default_credentials(self, mock_client_class, mock_auth_default):
        """Test initialization with default credentials."""
        mock_credentials = Mock()
        mock_project = "test-project"
        mock_auth_default.return_value = (mock_credentials, mock_project)

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        conn = ConnBigQuery()

        assert conn.credentials == mock_credentials
        assert conn.project == mock_project
        assert conn.client == mock_client
        mock_client_class.assert_called_once_with(
            credentials=mock_credentials, project=mock_project
        )


class TestConnBigQueryExecuteQuery:
    """Test execute_query method."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_query_basic(self, mock_client_class, mock_auth_default):
        """Test basic query execution."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_result = Mock()
        mock_query_job.result.return_value = mock_result
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.execute_query("SELECT 1")

        assert result == mock_result
        mock_client.query.assert_called_once_with("SELECT 1", job_config=None)
        mock_query_job.result.assert_called_once_with(timeout=None)

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_query_with_job_config(self, mock_client_class, mock_auth_default):
        """Test query execution with job config."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_result = Mock()
        mock_query_job.result.return_value = mock_result
        mock_client.query.return_value = mock_query_job

        job_config = bigquery.QueryJobConfig(use_legacy_sql=False)

        conn = ConnBigQuery()
        result = conn.execute_query("SELECT * FROM table", job_config=job_config)

        assert result == mock_result
        mock_client.query.assert_called_once_with("SELECT * FROM table", job_config=job_config)

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_query_with_timeout(self, mock_client_class, mock_auth_default):
        """Test query execution with timeout."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_result = Mock()
        mock_query_job.result.return_value = mock_result
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.execute_query("SELECT 1", timeout=30.0)

        assert result == mock_result
        mock_query_job.result.assert_called_once_with(timeout=30.0)


class TestConnBigQueryQueryData:
    """Test query_data method."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_query_data_returns_dataframe(self, mock_client_class, mock_auth_default):
        """Test query_data returns DataFrame by default."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock row objects
        mock_row1 = {"id": 1, "name": "Alice"}
        mock_row2 = {"id": 2, "name": "Bob"}
        mock_result = [mock_row1, mock_row2]

        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_result
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.query_data("SELECT * FROM users")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["id", "name"]

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_query_data_returns_list_of_dicts(self, mock_client_class, mock_auth_default):
        """Test query_data returns list of dicts when dataframe=False."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_row1 = {"id": 1, "name": "Alice"}
        mock_row2 = {"id": 2, "name": "Bob"}
        mock_result = [mock_row1, mock_row2]

        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_result
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.query_data("SELECT * FROM users", dataframe=False)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Alice"}
        assert result[1] == {"id": 2, "name": "Bob"}


class TestConnBigQueryExecuteDML:
    """Test execute_dml method."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_dml_insert(self, mock_client_class, mock_auth_default):
        """Test DML execution for INSERT statement."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_query_job.result.return_value = None
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        affected_rows = conn.execute_dml("INSERT INTO table VALUES (1, 'test')")

        assert affected_rows == 1
        mock_query_job.result.assert_called_once()

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_dml_update(self, mock_client_class, mock_auth_default):
        """Test DML execution for UPDATE statement."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_query_job.num_dml_affected_rows = 5
        mock_query_job.result.return_value = None
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        affected_rows = conn.execute_dml("UPDATE table SET name = 'updated'")

        assert affected_rows == 5

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_dml_delete(self, mock_client_class, mock_auth_default):
        """Test DML execution for DELETE statement."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_query_job.num_dml_affected_rows = 3
        mock_query_job.result.return_value = None
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        affected_rows = conn.execute_dml("DELETE FROM table WHERE id > 10")

        assert affected_rows == 3


class TestConnBigQueryExecuteDDL:
    """Test execute_ddl method."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_ddl_create_table(self, mock_client_class, mock_auth_default):
        """Test DDL execution for CREATE TABLE."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_query_job.result.return_value = None
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.execute_ddl("CREATE TABLE test (id INT64)")

        assert result is True
        mock_query_job.result.assert_called_once()

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_execute_ddl_drop_table(self, mock_client_class, mock_auth_default):
        """Test DDL execution for DROP TABLE."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_query_job = Mock()
        mock_query_job.result.return_value = None
        mock_client.query.return_value = mock_query_job

        conn = ConnBigQuery()
        result = conn.execute_ddl("DROP TABLE test")

        assert result is True


class TestConnBigQueryTableOperations:
    """Test table operation methods."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_table_exists_true(self, mock_client_class, mock_auth_default):
        """Test table_exists returns True when table exists."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client

        mock_table = Mock()
        mock_client.get_table.return_value = mock_table

        conn = ConnBigQuery()
        exists = conn.table_exists("my_dataset", "my_table")

        assert exists is True
        mock_client.get_table.assert_called_once_with("test-project.my_dataset.my_table")

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_table_exists_false(self, mock_client_class, mock_auth_default):
        """Test table_exists returns False when table doesn't exist."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client

        mock_client.get_table.side_effect = Exception("Table not found")

        conn = ConnBigQuery()
        exists = conn.table_exists("my_dataset", "my_table")

        assert exists is False

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_get_table_schema(self, mock_client_class, mock_auth_default):
        """Test get_table_schema returns schema fields."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client

        mock_schema = [
            bigquery.SchemaField("id", "INTEGER"),
            bigquery.SchemaField("name", "STRING"),
        ]
        mock_table = Mock()
        mock_table.schema = mock_schema
        mock_client.get_table.return_value = mock_table

        conn = ConnBigQuery()
        schema = conn.get_table_schema("my_dataset", "my_table")

        assert schema == mock_schema
        assert len(schema) == 2


class TestConnBigQueryListOperations:
    """Test list operation methods."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_list_datasets(self, mock_client_class, mock_auth_default):
        """Test list_datasets returns dataset IDs."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_dataset1 = Mock()
        mock_dataset1.dataset_id = "dataset1"
        mock_dataset2 = Mock()
        mock_dataset2.dataset_id = "dataset2"

        mock_client.list_datasets.return_value = [mock_dataset1, mock_dataset2]

        conn = ConnBigQuery()
        datasets = conn.list_datasets()

        assert datasets == ["dataset1", "dataset2"]
        mock_client.list_datasets.assert_called_once()

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_list_tables(self, mock_client_class, mock_auth_default):
        """Test list_tables returns table IDs."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_table1 = Mock()
        mock_table1.table_id = "table1"
        mock_table2 = Mock()
        mock_table2.table_id = "table2"
        mock_table3 = Mock()
        mock_table3.table_id = "table3"

        mock_client.list_tables.return_value = [mock_table1, mock_table2, mock_table3]

        conn = ConnBigQuery()
        tables = conn.list_tables("my_dataset")

        assert tables == ["table1", "table2", "table3"]
        mock_client.list_tables.assert_called_once_with("my_dataset")


class TestConnBigQueryContextManager:
    """Test context manager functionality."""

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_context_manager_enter(self, mock_client_class, mock_auth_default):
        """Test context manager __enter__ returns self."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        conn = ConnBigQuery()
        with conn as context:
            assert context is conn

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_context_manager_exit_calls_close(self, mock_client_class, mock_auth_default):
        """Test context manager __exit__ calls close."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        conn = ConnBigQuery()
        with conn:
            pass

        mock_client.close.assert_called_once()

    @patch("docbt.providers.conn_bigquery.google.auth.default")
    @patch("docbt.providers.conn_bigquery.bigquery.Client")
    def test_close_method(self, mock_client_class, mock_auth_default):
        """Test close method calls client.close()."""
        mock_auth_default.return_value = (Mock(), "test-project")
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        conn = ConnBigQuery()
        conn.close()

        mock_client.close.assert_called_once()
