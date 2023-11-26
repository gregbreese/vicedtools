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
"""Executable script for uploading compass student details to BigQuery."""

import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, STUDENT_DETAILS_SCHEMA,
                            STUDENT_DETAILS_CLUSTERING_FIELDS)
from vicedtools.scripts.config import (compass_dir, student_details_csv,
                                        student_details_table_id, gcs_bucket)


def main():
    temp_file = os.path.join(compass_dir, "temp.csv")

    details_df = pd.read_csv(student_details_csv,
                             keep_default_na=False,
                             dtype=str)
    details_df = details_df[details_df["Status"].isin(["Active",
                                                       "Left"])].copy()
    details_df.rename(columns={
        "SUSSI ID": "StudentCode",
        "First Name": "FirstName",
        "Preferred Name": "PrefName",
        "Last Name": "Surname",
        "Year Level": "YearLevel",
        "Form Group": "HomeGroup",
        "Date of birth": "DateOfBirth"
    },
                      inplace=True)

    details_df["Surname"] = details_df["Surname"].str.title()
    details_df["FirstName"] = details_df["FirstName"].str.title()
    details_df["PrefName"] = details_df["PrefName"].str.title()

    details_df["DateOfBirth"] = pd.to_datetime(details_df["DateOfBirth"],
                                               format="%d/%m/%Y")

    def year_level_number(yr_lvl_str):
        if yr_lvl_str:
            digits = yr_lvl_str[-2:]
            return int(digits)
        else:
            return ""

    details_df["YearLevel"] = details_df["YearLevel"].apply(year_level_number)

    columns = [
        "StudentCode", "Surname", "FirstName", "PrefName", "Gender",
        "YearLevel", "HomeGroup", "Status", "DateOfBirth"
    ]
    details_df[columns].to_csv(temp_file, index=False)

    upload_csv_to_bigquery(temp_file, STUDENT_DETAILS_SCHEMA,
                           STUDENT_DETAILS_CLUSTERING_FIELDS,
                           student_details_table_id, gcs_bucket)
    os.remove(temp_file)


if __name__ == "__main__":
    main()
