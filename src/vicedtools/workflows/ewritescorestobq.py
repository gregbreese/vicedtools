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
"""Executable script for uploading student's eWrite scores to BigQuery"""

import os

import pandas as pd

from vicedtools.gcp import (upload_csv_to_bigquery, EWRITE_SCORES_SCHEMA,
                            EWRITE_SCORES_CLUSTERING_FIELDS,
                            EWRITE_CRITERIA_SCHEMA,
                            EWRITE_CRITERIA_CLUSTERING_FIELDS)

if __name__ == "__main__":
    from config import (ewrite_scores_csv, ewrite_scores_table_id, 
                        ewrite_criteria_csv, ewrite_criteria_table_id, bucket)

    upload_csv_to_bigquery(ewrite_scores_csv, EWRITE_SCORES_SCHEMA,
                           EWRITE_SCORES_CLUSTERING_FIELDS, ewrite_scores_table_id, bucket)
    upload_csv_to_bigquery(ewrite_criteria_csv, EWRITE_CRITERIA_SCHEMA,
                           EWRITE_CRITERIA_CLUSTERING_FIELDS, ewrite_criteria_table_id, bucket)
