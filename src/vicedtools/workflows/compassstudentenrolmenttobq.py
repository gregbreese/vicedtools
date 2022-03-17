import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery,
                            STUDENT_ENROLMENTS_SCHEMA,
                            STUDENT_ENROLMENTS_CLUSTERING_FIELDS)


def compass_student_enrolments_to_bq(table_id: str, bucket: str, enrolments_dir: str):
    """Imports student enrolments to BQ from Compass SDS export.
    
    Args:
        table_id: The BQ table id for the enrolments data
        bucket: A GCS bucket for temporarily storing the csv for import into BQ.
        enrolments_dir: The directory containing the Compass SDS export.
    """
    student_enrolments_file = os.path.join(enrolments_dir, "StudentEnrollment.csv")
    temp_file = os.path.join(enrolments_dir, "temp.csv")
    
    student_enrollment_df = pd.read_csv(student_enrolments_file)
    student_enrollment_df.rename(columns={
        "SIS ID": "StudentCode",
    }, inplace=True)
    
    student_enrollment_df[['ClassGroupCode','Cycle']] = student_enrollment_df['Section SIS ID'].str.split('-',expand=True)
    columns = ["ClassGroupCode", "StudentCode"]
    student_enrollment_df[columns].to_csv(temp_file, index=False)
    
    upload_csv_to_bigquery(temp_file, STUDENT_ENROLMENTS_SCHEMA,
                           STUDENT_ENROLMENTS_CLUSTERING_FIELDS,
                           table_id, bucket)
    os.remove(temp_file)

if __name__ == "__main__":
    
    from config import (root_dir,
                        compass_folder,
                        sds_folder,
                        student_enrolments_table_id,
                        bucket)

    enrolments_dir = os.path.join(root_dir, compass_folder, sds_folder)

    compass_student_enrolments_to_bq(student_enrolments_table_id, bucket, enrolments_dir)