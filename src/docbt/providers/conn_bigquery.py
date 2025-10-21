"""A connector class to run SQL commands against Google BigQuery."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# Handle optional dependencies
try:
    import google.auth
    import pandas as pd
    from google.cloud import bigquery

    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    # Type checking imports to avoid errors in IDEs
    if TYPE_CHECKING:
        import google.auth
        import pandas as pd
        from google.cloud import bigquery


class ConnBigQuery:
    """A connector class to run SQL commands against Google BigQuery.

    Supports single authentication method:
    1. Google Cloud CLI authentication (default if no credentials provided)
    """

    def __init__(self):
        """Initialize the BigQuery connector.

        https://googleapis.dev/python/google-api-core/latest/auth.html

        Raises:
            ImportError: If google-cloud-bigquery is not installed
        """
        if not BIGQUERY_AVAILABLE:
            raise ImportError(
                "BigQuery connector is not installed. Install it with: pip install docbt[bigquery]"
            )

        # https://google-auth.readthedocs.io/en/latest/user-guide.html
        self.credentials, self.project = google.auth.default()
        self.client = bigquery.Client(credentials=self.credentials, project=self.project)

    def execute_query(
        self,
        query: str,
        job_config: bigquery.QueryJobConfig | None = None,
        timeout: float | None = None,
    ) -> bigquery.table.RowIterator:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string to execute.
            job_config: Optional job configuration.
            timeout: Timeout in seconds for the query.

        Returns:
            RowIterator with query results.
        """
        query_job = self.client.query(query, job_config=job_config)
        return query_job.result(timeout=timeout)

    def query_data(
        self,
        query: str,
        job_config: bigquery.QueryJobConfig | None = None,
        timeout: float | None = None,
        dataframe: bool = True,
    ) -> list[dict[str, Any]] | pd.DataFrame:
        """
        Execute a SQL query and return results either as a list of dicts or a DataFrame.

        Args:
            query: SQL query string to execute.
            job_config: Optional job configuration.
            timeout: Timeout in seconds for the query.
            dataframe: If True, return results as a pandas DataFrame

        Returns:
            List of dictionaries representing rows.
        """
        results = self.execute_query(query, job_config, timeout)
        data = [dict(row) for row in results]
        if dataframe:
            data = pd.DataFrame(data)
        return data

    def execute_dml(self, query: str, job_config: bigquery.QueryJobConfig | None = None) -> int:
        """
        Execute a DML statement (INSERT, UPDATE, DELETE) and return affected rows.

        Args:
            query: DML query string to execute.
            job_config: Optional job configuration.

        Returns:
            Number of affected rows.
        """
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for completion
        return query_job.num_dml_affected_rows

    def execute_ddl(self, query: str, job_config: bigquery.QueryJobConfig | None = None) -> bool:
        """
        Execute a DDL statement (CREATE, ALTER, DROP).

        Args:
            query: DDL query string to execute.
            job_config: Optional job configuration.

        Returns:
            True if successful.
        """
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for completion
        return True

    def table_exists(self, dataset_id: str, table_id: str) -> bool:
        """
        Check if a table exists.

        Args:
            dataset_id: Dataset ID.
            table_id: Table ID.

        Returns:
            True if table exists, False otherwise.
        """
        table_ref = f"{self.client.project}.{dataset_id}.{table_id}"
        try:
            self.client.get_table(table_ref)
            return True
        except Exception:
            return False

    def get_table_schema(self, dataset_id: str, table_id: str) -> list[bigquery.SchemaField]:
        """
        Get the schema of a table.

        Args:
            dataset_id: Dataset ID.
            table_id: Table ID.

        Returns:
            List of SchemaField objects.
        """
        table_ref = f"{self.client.project}.{dataset_id}.{table_id}"
        table = self.client.get_table(table_ref)
        return table.schema

    def list_datasets(self) -> list[str]:
        """
        List all datasets in the project.

        Returns:
            List of dataset IDs.
        """
        datasets = self.client.list_datasets()
        return [dataset.dataset_id for dataset in datasets]

    def list_tables(self, dataset_id: str) -> list[str]:
        """
        List all tables in a dataset.

        Args:
            dataset_id: Dataset ID.

        Returns:
            List of table IDs.
        """
        tables = self.client.list_tables(dataset_id)
        return [table.table_id for table in tables]

    def close(self):
        """Close the BigQuery client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
