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
"""Executable script for uploading a table of student's most recent PAT results to BigQuery."""

import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, PAT_MOST_RECENT_SCHEMA,
                            PAT_MOST_RECENT_CLUSTERING_FIELDS)
from vicedtools.scripts.config import (pat_most_recent_csv,
                                        pat_most_recent_table_id, gcs_bucket)


def main():
    temp_file = os.path.join(os.path.dirname(pat_most_recent_csv), "temp.csv")

    column_rename = {
        "Username": "StudentCode",
        "Maths Completed": "MathsDate",
        "Reading Completed": "ReadingDate",
        "Maths Year level (at time of test)": "MathsYearLevel",
        "Reading Year level (at time of test)": "ReadingYearLevel",
        "Maths Test form": "MathsTestForm",
        "Reading Test form": "ReadingTestForm",
        "Maths Score category": "MathsScoreCategory",
        "Reading Score category": "ReadingScoreCategory",
        "Maths Scale": "MathsScale",
        "Reading Scale": "ReadingScale"
    }

    fields = [f.name for f in PAT_MOST_RECENT_SCHEMA]

    df = pd.read_csv(pat_most_recent_csv)
    df.rename(columns=column_rename, inplace=True)
    df[fields].to_csv(temp_file, index=False)
    upload_csv_to_bigquery(temp_file, PAT_MOST_RECENT_SCHEMA,
                           PAT_MOST_RECENT_CLUSTERING_FIELDS,
                           pat_most_recent_table_id, gcs_bucket)
    os.remove(temp_file)


if __name__ == "__main__":
    main()
