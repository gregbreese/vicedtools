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
"""Executable script for uploading compass reports to BigQuery."""

import os

from vicedtools.gcp import (upload_csv_to_bigquery, REPORTS_SCHEMA,
                            REPORTS_CLUSTERING_FIELDS, REPORTS_SUMMARY_SCHEMA,
                            REPORTS_SUMMARY_CLUSTERING_FIELDS)

if __name__ == "__main__":
    from config import (root_dir, compass_folder, reports_csv,
                        reports_summary_csv, reports_table_id,
                        reports_summary_table_id, bucket)

    reports_file = os.path.join(root_dir, compass_folder, reports_csv)
    reports_summary_file = os.path.join(root_dir, compass_folder,
                                        reports_summary_csv)

    upload_csv_to_bigquery(reports_file, REPORTS_SCHEMA,
                           REPORTS_CLUSTERING_FIELDS, reports_table_id, bucket)
    upload_csv_to_bigquery(reports_summary_file, REPORTS_SUMMARY_SCHEMA,
                           REPORTS_SUMMARY_CLUSTERING_FIELDS,
                           reports_summary_table_id, bucket)
