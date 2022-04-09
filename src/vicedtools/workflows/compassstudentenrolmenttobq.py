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
"""Executable script for uploading compass enrolment details to BigQuery."""

import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, STUDENT_ENROLMENTS_SCHEMA,
                            STUDENT_ENROLMENTS_CLUSTERING_FIELDS)


def compass_student_enrolments_to_bq(table_id: str, bucket: str, sds_dir: str):
    """Imports student enrolments to BQ from Compass SDS export.
    
    Args:
        table_id: The BQ table id for the enrolments data
        bucket: A GCS bucket for temporarily storing the csv for import into BQ.
        sds_dir: The directory containing the Compass SDS export.
    """
    student_enrolments_file = os.path.join(sds_dir, "StudentEnrollment.csv")
    temp_file = os.path.join(sds_dir, "temp.csv")

    student_enrollment_df = pd.read_csv(student_enrolments_file)
    student_enrollment_df.rename(columns={
        "SIS ID": "StudentCode",
    },
                                 inplace=True)

    student_enrollment_df[[
        'ClassGroupCode', 'Cycle'
    ]] = student_enrollment_df['Section SIS ID'].str.split('-', expand=True)
    columns = ["ClassGroupCode", "StudentCode"]
    student_enrollment_df[columns].to_csv(temp_file, index=False)

    upload_csv_to_bigquery(temp_file, STUDENT_ENROLMENTS_SCHEMA,
                           STUDENT_ENROLMENTS_CLUSTERING_FIELDS, table_id,
                           bucket)
    os.remove(temp_file)


if __name__ == "__main__":

    from config import (sds_dir, student_enrolments_table_id, bucket)

    compass_student_enrolments_to_bq(student_enrolments_table_id, bucket,
                                     sds_dir)
