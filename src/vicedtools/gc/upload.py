import pandas as pd
from google.cloud import storage
from google.cloud import bigquery

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


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the gc bucket.
    
    Arguments
    bucket_name: name of gc storage bucket
    source_file_name: path of local file
    destination_blob_name: name of destination gc storage blob
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print("File {} uploaded to {}.".format(source_file_name,
                                           destination_blob_name))


def update_table(schema, clustering_fields, uri, table_id):
    '''Updates a table in bigquery.
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


def upload_student_details(source_file, table_id, bucket):
    '''Updates a students details table in bigquery.

    Arguments
    source_file: the student details csv file
    table_id: the bigquery table_id of your student details table
    bucket: the name of your GC storage bucket
    '''
    blob_name = "student details/student details.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(STUDENT_DETAILS_SCHEMA, STUDENT_DETAILS_CLUSTERING_FIELDS, uri,
                 table_id)


def upload_reports(source_file, table_id, bucket):
    '''Updates a reports table in bigquery.

    Arguments
    source_file: the reports csv file
        e.g. from vicedtools.compass.Reports.saveReports(source_file)
    table_id: the bigquery table_id of your student details table
    bucket: the name of your GC storage bucket
    '''
    blob_name = "reports/reports.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(REPORTS_SCHEMA, REPORTS_CLUSTERING_FIELDS, uri, table_id)


def upload_reports_summary(source_file, table_id, bucket):
    '''Updates a reports summary table in bigquery.

    Arguments
    source_file: the reports csv file
        e.g. from vicedtools.compass.Reports.saveSummary(source_file)
    table_id: the bigquery table_id of your student details table
    bucket: the name of your GC storage bucket
    '''
    blob_name = "reports/reports_summary.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(REPORTS_SUMMARY_SCHEMA, REPORTS_SUMMARY_CLUSTERING_FIELDS, uri,
                 table_id)
