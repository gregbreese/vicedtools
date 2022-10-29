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

from vicedtools.gcp import (upload_csv_to_bigquery, NAPLAN_OUTCOMES_SCHEMA,
                            NAPLAN_OUTCOMES_CLUSTERING_FIELDS)

if __name__ == "__main__":
    from config import (naplan_outcomes_combined_csv, naplan_outcomes_table_id,
                        bucket)

    upload_csv_to_bigquery(naplan_outcomes_combined_csv, NAPLAN_OUTCOMES_SCHEMA,
                           NAPLAN_OUTCOMES_CLUSTERING_FIELDS,
                           naplan_outcomes_table_id, bucket)
