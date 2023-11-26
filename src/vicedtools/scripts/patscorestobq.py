#!/usr/bin/env python

# Copyright 2023 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Executable script for uploading student's PAT scores to BigQuery"""

import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, PAT_SCORES_SCHEMA,
                            PAT_SCORES_CLUSTERING_FIELDS)
from vicedtools.scripts.config import (pat_scores_csv, pat_scores_table_id,
                                        gcs_bucket)


def main():
    temp_file = os.path.join(os.path.dirname(pat_scores_csv), "temp.csv")

    column_rename = {
        "Username": "StudentCode",
        "Completed": "Date",
        "Year level (at time of test)": "YearLevel",
        "Test form": "TestForm",
        "Score category": "ScoreCategory"
    }
    fields = [f.name for f in PAT_SCORES_SCHEMA]

    df = pd.read_csv(pat_scores_csv)
    df.rename(columns=column_rename, inplace=True)
    df[fields].to_csv(temp_file, index=False)
    upload_csv_to_bigquery(temp_file, PAT_SCORES_SCHEMA,
                           PAT_SCORES_CLUSTERING_FIELDS, pat_scores_table_id,
                           gcs_bucket)
    os.remove(temp_file)


if __name__ == "__main__":
    main()
