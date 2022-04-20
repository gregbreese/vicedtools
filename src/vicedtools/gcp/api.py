# Copyright 2021 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for uploading data to GCP."""

from __future__ import annotations

from google.cloud import storage
from google.cloud import bigquery


def upload_csv_to_bigquery(source_file: str,
                           schema: dict[bigquery.SchemaField],
                           clustering_fields: list[str],
                           table_id: str,
                           bucket_name: str,
                           blob_name: str = "temp.csv") -> None:
    """Uploads a CSV to BigQuery via GSC.

    Uploads the file to GSC, imports it into BigQuery and then deletes the file
    from GSC.
    
    Args:
        source_file: The path to the csv file to import.
        schema: The BigQuery schema to use.
        clustering_fields: A list of fields to use for clustering.
        table_id: The BigQuery table_id to use.
        bucket_name: The name of the GSC bucket to use as an intermediary for the
            import.
        blob_name: The name of the GSC blob to use when uploading the source
            file to GSC.
    """
    # upload file to GCS
    uri = "gs://" + bucket_name + "/" + blob_name
    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.upload_from_filename(source_file)
    print(f"File {source_file} uploaded to {blob_name}.")

    # update table in BQ
    bq_client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        clustering_fields=clustering_fields,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)
    load_job = bq_client.load_table_from_uri(uri,
                                             table_id,
                                             job_config=job_config)
    load_job.result()  # Waits for the job to complete.
    destination_table = bq_client.get_table(table_id)
    print(table_id)
    print(f"Loaded {destination_table.num_rows} rows.")

    # delete blob from GCS
    blob.delete()
