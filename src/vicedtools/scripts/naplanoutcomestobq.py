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
"""Executable script for uploading NAPLAN outcomes BigQuery."""

from vicedtools.gcp import (upload_csv_to_bigquery, NAPLAN_OUTCOMES_SCHEMA,
                            NAPLAN_OUTCOMES_CLUSTERING_FIELDS,
                            NAPLAN_OUTCOMES_MOST_RECENT_CLUSTERING_FIELDS)
from vicedtools.scripts._config import (naplan_outcomes_combined_csv,
                                        naplan_outcomes_most_recent_csv,
                                        naplan_outcomes_table_id, 
                                        naplan_outcomes_most_recent_table_id,
                                        gcs_bucket)


def main():
    upload_csv_to_bigquery(naplan_outcomes_combined_csv, NAPLAN_OUTCOMES_SCHEMA,
                           NAPLAN_OUTCOMES_CLUSTERING_FIELDS,
                           naplan_outcomes_table_id, gcs_bucket)
    upload_csv_to_bigquery(naplan_outcomes_most_recent_csv, NAPLAN_OUTCOMES_SCHEMA,
                           NAPLAN_OUTCOMES_MOST_RECENT_CLUSTERING_FIELDS,
                           naplan_outcomes_most_recent_table_id, gcs_bucket)


if __name__ == "__main__":
    main()
