import os
import sys
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from utils.logger import setup_logger
from utils.config import load_env_variables, get_bigquery_credentials_path

class Big_Query_Loader:
    """
    Handles interactions with Google BigQuery, including connecting to the client,
    dataset management, loading DataFrames into tables, and executing SQL.
    """

    def __init__(self):
        self.logger = setup_logger(__name__)
        try:
            load_env_variables()
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = get_bigquery_credentials_path()
            self.client = bigquery.Client()
            self.logger.info(f"Successfully initialized BigQuery Client, project: '{self.client.project}'.")
        except Exception as e:
            self.logger.critical(f"Failed to connect to BigQuery: {e}")
            raise e

    def check_dataset_available(self, new_dataset_id, data_location='US'):
        """Checks if a dataset exists; creates it if it does not."""
        try:
            dataset_ref = f"{self.client.project}.{new_dataset_id}"
            try:
                self.client.get_dataset(dataset_ref)
                self.logger.info(f"Dataset '{new_dataset_id}' already exists.")
            except Exception:
                self.logger.info(f"Dataset '{new_dataset_id}' not found. Creating...")
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = data_location
                self.client.create_dataset(dataset)
                self.logger.info(f"Successfully created dataset: {new_dataset_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error in check_dataset_available: {e}")
            raise e

    def load_dataframe(self, df, dataset_id, bq_table_name,
                       write_disposition='WRITE_TRUNCATE',
                       partition_by=None, cluster_by=None):
        """
        Loads a Pandas DataFrame into a BigQuery table.
        Automatically detects partition field type:
          - DATE/TIMESTAMP columns → TimePartitioning
          - INTEGER columns (e.g. date keys like 20240101) → RangePartitioning
        """
        if df.empty:
            self.logger.warning(f"DataFrame for '{bq_table_name}' is empty. Skipping upload.")
            return

        destination_table = f"{self.client.project}.{dataset_id}.{bq_table_name}"

        job_config = bigquery.LoadJobConfig(
            write_disposition=getattr(bigquery.WriteDisposition, write_disposition)
        )

        if partition_by:
            # Detect whether partition field is integer (date key) or datetime
            if partition_by in df.columns and pd.api.types.is_integer_dtype(df[partition_by]):
                # Integer date key (e.g. 20240101) → RangePartitioning
                job_config.range_partitioning = bigquery.RangePartitioning(
                    field=partition_by,
                    range_=bigquery.PartitionRange(
                        start=19000101,
                        end=21001231,
                        interval=1
                    )
                )
                self.logger.info(f"Using RangePartitioning on integer field '{partition_by}'")
            else:
                # DATE or TIMESTAMP field → TimePartitioning
                job_config.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field=partition_by
                )
                self.logger.info(f"Using TimePartitioning on datetime field '{partition_by}'")

        if cluster_by:
            job_config.clustering_fields = cluster_by

        try:
            job = self.client.load_table_from_dataframe(df, destination_table, job_config=job_config)
            job.result()
            self.logger.info(f"Successfully loaded {len(df)} rows into '{bq_table_name}'")
        except Exception as e:
            self.logger.error(f"Failed to load data into BigQuery table '{bq_table_name}': {e}")
            raise e

    def execute_query(self, sql_query: str):
        """Executes a raw SQL query on BigQuery."""
        try:
            self.logger.info("Executing custom SQL query...")
            query_job = self.client.query(sql_query)
            result = query_job.result()
            self.logger.info("SQL query executed successfully.")
            return result
        except Exception as e:
            self.logger.error(f"Failed to execute SQL: {e}")
            raise e