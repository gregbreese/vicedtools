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
"""Utilities for uploading data to GC."""

from google.cloud import storage
from google.cloud import bigquery
import pandas as pd

STUDENT_DETAILS_SCHEMA = [
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Surname", "STRING"),
    bigquery.SchemaField("FirstName", "STRING"),
    bigquery.SchemaField("PrefName", "STRING"),
    bigquery.SchemaField("Gender", "STRING"),
    bigquery.SchemaField("YearLevel", "STRING"),
    bigquery.SchemaField("HomeGroup", "STRING"),
]
STUDENT_DETAILS_CLUSTERING_FIELDS = [
    "StudentCode", "YearLevel", "HomeGroup", "Gender"
]

REPORTS_SCHEMA = [
    bigquery.SchemaField("Time", "DATE"),
    bigquery.SchemaField("ClassCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("ResultName", "STRING"),
    bigquery.SchemaField("ResultGrade", "STRING"),
    bigquery.SchemaField("ResultScore", "FLOAT"),
    bigquery.SchemaField("Type", "STRING"),
    bigquery.SchemaField("SubjectName", "STRING"),
    bigquery.SchemaField("SubjectCode", "STRING"),
    bigquery.SchemaField("LearningArea", "STRING"),
    bigquery.SchemaField("TeacherCode", "STRING")
]
REPORTS_CLUSTERING_FIELDS = ["StudentCode", "Time", "LearningArea", "Type"]

REPORTS_SUMMARY_SCHEMA = [
    bigquery.SchemaField("Time", "DATE"),
    bigquery.SchemaField("ClassCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("SubjectCode", "STRING"),
    bigquery.SchemaField("SubjectName", "STRING"),
    bigquery.SchemaField("LearningArea", "STRING"),
    bigquery.SchemaField("TeacherCode", "STRING"),
    bigquery.SchemaField("Academic", "FLOAT"),
    bigquery.SchemaField("Work_Habits", "FLOAT"),
]
REPORTS_SUMMARY_CLUSTERING_FIELDS = [
    "StudentCode", "Time", "LearningArea", "TeacherCode"
]


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


def upload_student_details(source_file: str, table_id: str,
                           bucket: str) -> None:
    '''Updates a students details table in bigquery.

    Takes a student details csv file as produced from 
        vicedtools.gc.format.create_student_details_gc_csv(...)
    and uploads to under 
        ./student details/student details.csv 
    in the given GCS bucket.

    Args:
        source_file: The path of the student details csv file.
        table_id: The bigquery table ID of the student details table.
        bucket: The name of the GC storage bucket.
    '''
    blob_name = "student details/student details.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(STUDENT_DETAILS_SCHEMA, STUDENT_DETAILS_CLUSTERING_FIELDS, uri,
                 table_id)


def upload_reports(source_file: str, table_id: str, bucket: str) -> None:
    '''Updates a reports table in bigquery.

    Takes a reports csv as produced from
        vicedtools.compass.Reports.saveReports(source_file)
    and uploads it under
        ./reports/reports.csv
    in the given GCS bucket.

    Args:
        source_file: The path of the reports csv file.
        table_id: The bigquery table ID of the student details table.
        bucket: The name of the GC storage bucket.
    '''
    blob_name = "reports/reports.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(REPORTS_SCHEMA, REPORTS_CLUSTERING_FIELDS, uri, table_id)


def upload_reports_summary(source_file: str, table_id: str,
                           bucket: str) -> None:
    '''Updates a reports summary table in bigquery.

    Takes a reports csv as produced from
        vicedtools.compass.Reports.saveSummary(source_file)
    and uploads it under
        ./reports/reports.csv
    in the given GCS bucket.

    Args:
        source_file: The path of the reports summary csv file.
        table_id: The bigquery table ID of the student details table.
        bucket: The name of the GC storage bucket.
    '''
    blob_name = "reports/reports_summary.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(REPORTS_SUMMARY_SCHEMA, REPORTS_SUMMARY_CLUSTERING_FIELDS, uri,
                 table_id)
