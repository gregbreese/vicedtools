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
"""Executable script for uploading compass enrolment details to BigQuery."""

import json
import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, STUDENT_ENROLMENTS_SCHEMA,
                            STUDENT_ENROLMENTS_CLUSTERING_FIELDS)
from vicedtools.scripts._config import (academic_groups_json, compass_dir,
                                        enrolment_details_dir,
                                        student_enrolments_table_id, gcs_bucket)


def main():
    # Create current enrolment list from enrolments in current Academic cycle.

    with open(academic_groups_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)

    for c in cycles:
        if c['isRelevant']:
            cycle_name = c['name']
            break

    enrolments_file = os.path.join(enrolment_details_dir,
                                   f"{cycle_name} enrolments.csv")
    current_enrolments = pd.read_csv(enrolments_file)
    # Just take StudentCode and ClassCode columns
    current_enrolments = current_enrolments[["ii", "name"]]
    column_renaming = {"ii": "StudentCode", "name": "ClassCode"}
    current_enrolments.rename(columns=column_renaming, inplace=True)

    temp_file = os.path.join(compass_dir, "temp.csv")
    current_enrolments.to_csv(temp_file, index=False)

    upload_csv_to_bigquery(temp_file, STUDENT_ENROLMENTS_SCHEMA,
                           STUDENT_ENROLMENTS_CLUSTERING_FIELDS,
                           student_enrolments_table_id, gcs_bucket)


if __name__ == "__main__":
    main()
