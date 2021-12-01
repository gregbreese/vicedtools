# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vicedtools.automation.compass import export_reports
from vicedtools.automation.gcp import upload_to_bigquery
from vicedtools.automation.gcpschema import (
    STUDENT_DETAILS_SCHEMA, STUDENT_DETAILS_CLUSTERING_FIELDS, REPORTS_SCHEMA,
    REPORTS_CLUSTERING_FIELDS, REPORTS_SUMMARY_SCHEMA,
    REPORTS_SUMMARY_CLUSTERING_FIELDS, NAPLAN_SCHEMA, NAPLAN_CLUSTERING_FIELDS,
    GAT_SCHEMA, GAT_CLUSTERING_FIELDS)
