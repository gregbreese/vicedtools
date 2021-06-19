import pandas as pd
from google.cloud import storage
from google.cloud import bigquery

STUDENT_DETAILS_SCHEMA=[
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Surname", "STRING"),
    bigquery.SchemaField("FirstName", "STRING"),
    bigquery.SchemaField("PrefName", "STRING"),
    bigquery.SchemaField("Gender", "STRING"),
    bigquery.SchemaField("YearLevel", "STRING"),
    bigquery.SchemaField("HomeGroup", "STRING"),
]
STUDENT_DETAILS_CLUSTERING_FIELDS = ["StudentCode", 
                                        "YearLevel", 
                                        "HomeGroup", 
                                        "Gender"]


def create_student_details_gc_csv(compass_student_details, save_path):
    '''Creates a csv for uploading to gc.

    Arguments
    compass_student_details: a student details export csv from Compass. Can be 
        downloaded using vicedtools.compass.export_student_details or directly
        from https://###.compass.education/Services/FileDownload/CsvRequestHandler?type=37
    save_path: the path to save the csv
    '''
    details_df = pd.read_csv(compass_student_details)
    details_df = details_df[details_df["Status"] == "Active"].copy()
    details_df.rename(columns={"SUSSI ID":"StudentCode",
                                "First Name":"FirstName", 
                                "Preferred Name":"PrefName", 
                                "Last Name":"Surname", 
                                "Year Level":"YearLevel", 
                                "Form Group":"HomeGroup"}, 
                                inplace=True)
    details_df["Surname"] = details_df["Surname"].str.title()
    def year_level_number(yr_lvl_str):
        digits = yr_lvl_str[-2:]
        return int(digits)
    details_df["YearLevel"] = details_df["YearLevel"].apply(year_level_number)
    columns = ["StudentCode","Surname","FirstName","PrefName","Gender", "YearLevel", "HomeGroup"]
    details_df[columns].to_csv(save_path, index=False)

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
    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )
    
def update_table( schema, clustering_fields, uri, table_id):
    '''Updates a table in bigquery.
    '''
    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        clustering_fields=clustering_fields,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    load_job = client.load_table_from_uri(
        uri, table_id, job_config=job_config
    )  # Make an API request.

    load_job.result()  # Waits for the job to complete.

    destination_table = client.get_table(table_id)  # Make an API request.
    print(table_id)
    print("Loaded {} rows.".format(destination_table.num_rows))

def update_student_details_table(source_file, table_id, bucket):
    '''Updates a students details table in bigquery.

    Arguments
    source_file: the student details csv file
    table_id: the bigquery table_id of your student details table
    bucket: the name of your GC storage bucket
    '''
    blob_name = "student details/student details.csv"
    uri = "gs://" + bucket + "/" + blob_name
    upload_blob(bucket, source_file, blob_name)
    update_table(STUDENT_DETAILS_SCHEMA, STUDENT_DETAILS_CLUSTERING_FIELDS, uri, table_id)