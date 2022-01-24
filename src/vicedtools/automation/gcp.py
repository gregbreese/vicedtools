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

from vicedtools.automation.gcpschema import (
    STUDENT_DETAILS_SCHEMA, STUDENT_DETAILS_CLUSTERING_FIELDS, 
    STUDENT_CLASS_RELATIONSHIPS_SCHEMA, REPORTS_SCHEMA,
    STUDENT_CLASS_RELATIONSHIPS_CLUSTERING_FIELDS,
    REPORTS_CLUSTERING_FIELDS, REPORTS_SUMMARY_SCHEMA,
    REPORTS_SUMMARY_CLUSTERING_FIELDS, NAPLAN_SCHEMA, NAPLAN_CLUSTERING_FIELDS,
    GAT_SCHEMA, GAT_CLUSTERING_FIELDS)


def upload_blob(bucket_name: str, source_file_name: str,
                destination_blob_name: str) -> None:
    """Uploads a file to the gc bucket.

    Copied from
    https://github.com/GoogleCloudPlatform/python-docs-samples/blob/HEAD/storage/cloud-client/storage_upload_file.py
    
    Args:
        bucket_name: The name of the GC storage bucket
        source_file_name: The path of local file to upload
        destination_blob_name: The Name of destination GC storage blob
    """

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print("File {} uploaded to {}.".format(source_file_name,
                                           destination_blob_name))


def update_table(schema: list[bigquery.SchemaField],
                 clustering_fields: list[str], uri: str, table_id: str) -> None:
    '''Updates a table in bigquery.

    Copied from
    https://github.com/googleapis/python-bigquery/blob/35627d145a41d57768f19d4392ef235928e00f72/samples/load_table_uri_csv.py

    Args:
        schema: A list of bigquery.SchemaField to define to schema
        clustering_fields: A list of up to four names of fields
        uri: The GC uri to upload the file from
            E.g. "gs://cloud-samples-data/bigquery/us-states/us-states.csv"
        table_id: The BigQuery table ID.
            E.g. "your-project.your_dataset.your_table_name
    '''

    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        clustering_fields=clustering_fields,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)

    load_job = client.load_table_from_uri(
        uri, table_id, job_config=job_config)  # Make an API request.

    load_job.result()  # Waits for the job to complete.

    destination_table = client.get_table(table_id)  # Make an API request.
    print(table_id)
    print("Loaded {} rows.".format(destination_table.num_rows))


def delete_blob(bucket_name: str, blob_name: str) -> None:
    """Deletes a blob from the bucket.

    Copied from
    https://cloud.google.com/storage/docs/deleting-objects#code-samples
    """
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


def upload_csv_to_bigquery(source_file: str,
                       schema: dict[bigquery.SchemaField],
                       clustering_fields: list[str],
                       table_id: str,
                       bucket: str,
                       blob_name: str = "temp.csv") -> None:
    """Generic uploader to BigQuery via GSC.

    Uploads the file to GSC, imports it into BigQuery and then deletes the file
    from GSC.
    
    Args:
        source_file: The path to the csv file to import.
        schema: The BigQuery schema to use.
        clustering_fields: A list of fields to use for clustering.
        table_id: The BigQuery table_id to use.
        bucket: The name of the GSC bucket to use as an intermediary for the
            import.
        blob_name: The name of the GSC blob to use when uploading the source
            file to GSC.
    """
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(schema, clustering_fields, uri, table_id)
    delete_blob(bucket, blob_name)
