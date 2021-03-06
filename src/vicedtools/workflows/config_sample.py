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
"""A sample configuration file."""

from __future__ import annotations

import os

import numpy as np
from pandas.api.types import CategoricalDtype

# root folder for storing downloads
root_dir = "."

# vass
vass_grid_password = [('1', '1'), ('8', '1'), ('4', '5'), ('5', '5'),
                      ('1', '8'), ('8', '8')]
vass_username = ""
vass_password = """"""

# compass
from vicedtools.compass.compasssession import CompassBasicAuthenticator
compass_username = ""
compass_password = """"""
compass_authenticator = CompassBasicAuthenticator(compass_username,
                                                   compass_password)
compass_school_code = "gwsc-vic"

# naplan
from vicedtools.naplan.dataservicesession import DataServiceBasicAuthenticator
dataservice_username = ""
dataservice_password = ""
dataservice_authenticator = DataServiceBasicAuthenticator(
    dataservice_username, dataservice_password)

# OARS (ACER tests)
from vicedtools.acer import OARSBasicAuthenaticator
oars_username = ""
oars_password = """"""
oars_authenticator = OARSBasicAuthenaticator(oars_username, oars_password)
oars_school_code = ""

# default vass directory structure
vass_folder = "vass exports"
vass_dir = os.path.join(root_dir, vass_folder)
vass_student_details_dir = os.path.join(vass_dir, "personal details summary")
vass_school_program_dir = os.path.join(vass_dir, "school program summary")
vass_predicted_scores_dir = os.path.join(vass_dir, "predicted scores")
vass_school_scores_dir = os.path.join(vass_dir, "school scores")
vass_gat_scores_dir = os.path.join(vass_dir, "gat scores")
vass_external_scores_dir = os.path.join(vass_dir, "external scores")
vass_moderated_coursework_scores_dir = os.path.join(
    vass_dir, "moderated coursework scores")

# default compass directory structure
compass_dir = os.path.join(root_dir, "compass exports")
student_details_csv = os.path.join(compass_dir, "student details",
                                   "student details.csv")
student_household_information_csv = os.path.join(
    compass_dir, "student details", "student household information.csv")
sds_dir = os.path.join(compass_dir, "SDS export")
subjects_dir = os.path.join(compass_dir, "subjects")
progress_reports_dir = os.path.join(compass_dir, "progress reports")
learning_tasks_dir = os.path.join(compass_dir, "learning tasks")
reports_dir = os.path.join(compass_dir, "reports")
academic_groups_json = os.path.join(compass_dir, "academic groups.json")
progress_report_cycles_json = os.path.join(compass_dir,
                                           "progress report cycles.json")
report_cycles_json = os.path.join(compass_dir, "report cycles.json")
# locations for saving files of combined report data
reports_file = os.path.join(compass_dir, "reports.csv")
reports_summary_file = os.path.join(compass_dir, "reports_summary.csv")

# default directory structure for NAPLAN exports
naplan_dir = os.path.join(root_dir, "napla exports")
naplan_outcomes_dir = os.path.join(naplan_dir, "outcomes exports")
naplan_sssr_dir = os.path.join(naplan_dir, "sssr exports")

# default directory structure for OARS exports
oars_dir = os.path.join(root_dir, "OARS exports")
oars_staff_xlsx = os.path.join(oars_dir, f"{oars_school_code}-staff.xlsx")
oars_candidates_json = os.path.join(oars_dir, "candidates.json")
pat_sittings_dir = os.path.join(oars_dir, "PAT sittings")
oars_tests_json = os.path.join(oars_dir, "tests.json")
scale_constructs_json = os.path.join(oars_dir, "scaleconstructs.json")
# files for combined PAT data
pat_scores_csv = os.path.join(oars_dir, "pat scores.csv")
pat_most_recent_csv = os.path.join(oars_dir, "pat most recent.csv")

# Google Cloud Platform settings for uploading data to use with Data Studio
gcp_project = "abc-school-data"
general_dataset = "general_dataset"
vce_dataset = "vce_dataset"
gcs_bucket = "abc-school-bucket"

#default table structure
student_details_table_id = f"{gcp_project}.{general_dataset}.student_details"
student_enrolments_table_id = f"{gcp_project}.{general_dataset}.student_enrolments"
pat_scores_table_id = f"{gcp_project}.{general_dataset}.pat_scores"
pat_most_recent_table_id = f"{gcp_project}.{general_dataset}.pat_most_recent"
naplan_outcomes_table_id = f"{gcp_project}.{general_dataset}.naplan"
reports_table_id = f"{gcp_project}.{general_dataset}.reports"
reports_summary_table_id = f"{gcp_project}.{general_dataset}.reports_summary"
gat_table_id = f"{gcp_project}.{general_dataset}.gat"
ewrite_scores_table_id = f"{gcp_project}.{general_dataset}.ewrite_scores"
ewrite_criteria_table_id = f"{gcp_project}.{general_dataset}.ewrite_criteria"
vce_study_scores_table_id = f"{gcp_project}.{vce_dataset}.study_scores"
vce_adjusted_scores_table_id = f"{gcp_project}.{vce_dataset}.adjusted_scores"

# Functions to support the summarising of reporting data exported from COmpass

# A CSV with SubjectCode, SubjectName, LearningArea columns with metadata
# for each subject in the school. Used for adding Learning Area data to
# report summaries.
subjects_file = "./subjects metadata.csv"

# Replace subject names or grade names when combining report data.
# Useful with subject names or grade names have changed over the years
# but you want to treat them the same.
replace_values = {
    "SubjectName": {
        "11 Computing": "11 Applied Computing"
    },
    "Result": {
        "Needs Improvement": "Below Standard",
    }
}
# Replace subject codes
# Useful when subject codes have changed over the years but you want to
# compare over time
replace_subject_codes = {
    "SubjectCode": {
        "GTR": "GTAR",
        "GUITAR": "GTAR",
    }
}

# The order of all report/progress report grade labels.
grade_order = [
    "Exempt", "Modified", "Not Demonstrated", "Unsatisfactory", "Rarely",
    "Below Standard", "Satisfactory", "Sometimes", "Competent", "Good",
    "Very Good", "Usually", "Excellent", "Consistently", "Outstanding"
]
results_dtype = CategoricalDtype(categories=grade_order, ordered=True)

# The text names for progress report times to use as work habits.
progress_report_items = [
    "Completes all set learning", "Contribution in class", "Perseverance",
    "Ready to learn", "Respectfully works/communicates with others",
    "Uses feedback to improve"
]

# Functions for mapping grades to numerical scores for aggregation
def learning_tasks_result_mapper(result: str) -> float:
    """Maps report grade labels to a score."""
    if result == "Not Demonstrated":
        return 0.35
    if result == "Below Standard":
        return 0.46
    if result == "Satisfactory":
        return 0.55
    if result == "Competent":
        return 0.64
    if result == "Good":
        return 0.73
    if result == "Very Good":
        return 0.82
    if result == "Excellent":
        return 0.91
    if result == "Outstanding":
        return 1.0
    return float('nan')

def work_habits_result_mapper(result: str) -> float:
    """Maps work habit grade labels to a score."""
    if result == "Unsatisfactory":
        return 0.35
    if result == "Satisfactory":
        return 0.55
    if result == "Good":
        return 0.73
    if result == "Very Good":
        return 0.82
    if result == "Excellent":
        return 1.0
    return np.nan

def progress_report_result_mapper(result: str) -> float:
    """Maps progress report grade labels to a score."""
    if result == "Rarely":
        return 0.25
    if result == "Sometimes":
        return 0.5
    if result == "Usually":
        return 0.75
    if result == "Consistently":
        return 1.0
    return np.nan
