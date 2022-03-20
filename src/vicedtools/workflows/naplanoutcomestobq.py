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
"""Executable script for uploading NAPLAN outcomes BigQuery."""

import glob
import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery,
                            NAPLAN_OUTCOMES_SCHEMA,
                            NAPLAN_OUTCOMES_CLUSTERING_FIELDS)

def naplan_outcomes_to_bq(table_id: str, bucket: str, naplan_dir: str, keep_combined_file: bool = False):
    """Merges NAPLAN outcomes exports and uploads a combined table to Bigquery.
    
    Args:
        table_id: The BQ table id for the NAPLAN data
        bucket: A GCS bucket for temporarily storing the csv for import into BQ.
        naplan_dir: The folder containing the outcomes exports.
        keep_combined_file: If True, save a csv containing the merged outcomes exports.
    """
    files = glob.glob(naplan_dir + "*Outcome*.csv")
    columns = ["APS Year","Reporting Test","First Name","Second Name","Surname","READING_nb","WRITING_nb","SPELLING_nb","NUMERACY_nb","GRAMMAR & PUNCTUATION_nb","Class","Date of Birth","Gender","LBOTE","ATSI","Home School Name","Reporting School Name","Cases ID"]
    df = pd.DataFrame(columns=columns)

    for f in files:
        temp_df = pd.read_csv(f)
        if len(temp_df.columns) == 18 and temp_df.columns[0] == "APS Year":
            temp_df.columns = columns
            df = pd.concat([df,temp_df])
    combined_file = os.path.join(naplan_dir, "NAPLAN combined.csv")
    df[columns].to_csv(combined_file, index=False)

    upload_csv_to_bigquery(combined_file, NAPLAN_OUTCOMES_SCHEMA, 
                       NAPLAN_OUTCOMES_CLUSTERING_FIELDS,
                       table_id, bucket)
    if not keep_combined_file:
        os.remove(combined_file)


if __name__ == "__main__":
    from config import (root_dir,
                        naplan_folder,
                        naplan_outcomes_folder,
                        naplan_outcomes_table_id,
                        bucket)
    naplan_dir = os.path.join(root_dir, naplan_folder, naplan_outcomes_folder)
    naplan_outcomes_to_bq(naplan_outcomes_table_id, bucket, naplan_dir)
