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

import re
import os

import pandas as pd
import tomli

from vicedtools import CompassBasicAuthenticator, OARSBasicAuthenticator, VASSBasicAuthenticator

if 'VICEDTOOLS_CONFIG' in os.environ:
    config_file = os.environ['VICEDTOOLS_CONFIG']
else:
    raise RuntimeError("VICEDTOOLS_CONFIG environment variable not defined.")

with open(config_file, "rb") as f:
    config = tomli.load(f)

root_dir = config['root_dir']

# vass
vass_authenticator = VASSBasicAuthenticator(config['vass']['username'],
                                            config['vass']['password'],
                                            config['vass']['grid_password'])

vass_dir = os.path.join(root_dir, config['vass']['dir'])
vass_student_details_dir = os.path.join(vass_dir,
                                        config['vass']["student_details_dir"])
vass_school_program_dir = os.path.join(vass_dir,
                                       config['vass']["school_program_dir"])
vass_predicted_scores_dir = os.path.join(vass_dir,
                                         config['vass']["predicted_scores_dir"])
vass_school_scores_dir = os.path.join(vass_dir,
                                      config['vass']["school_scores_dir"])
vass_gat_scores_dir = os.path.join(vass_dir, config['vass']["gat_scores_dir"])
vass_external_scores_dir = os.path.join(vass_dir,
                                        config['vass']["external_scores_dir"])
vass_moderated_coursework_scores_dir = os.path.join(
    vass_dir, config['vass']["moderated_coursework_scores_dir"])

# compass
compass_authenticator = CompassBasicAuthenticator(config['compass']['username'],
                                                  config['compass']['password'])
compass_school_code = config['compass']['school_code']
compass_dir = os.path.join(root_dir, config['compass']['dir'])
academic_groups_json = os.path.join(compass_dir,
                                    config['compass']['academic_groups_json'])
progress_report_cycles_json = os.path.join(
    compass_dir, config['compass']['progress_report_cycles_json'])
report_cycles_json = os.path.join(compass_dir,
                                  config['compass']['report_cycles_json'])
student_details_dir = os.path.join(compass_dir,
                                   config['compass']['student_details_dir'])
student_details_csv = os.path.join(student_details_dir,
                                   config['compass']['student_details_csv'])
student_household_information_csv = os.path.join(
    student_details_dir, config['compass']['student_household_information_csv'])
subjects_dir = os.path.join(compass_dir, config['compass']['subjects_dir'])
class_details_dir = os.path.join(compass_dir,
                                 config['compass']['class_details_dir'])
enrolment_details_dir = os.path.join(compass_dir,
                                     config['compass']['enrolment_details_dir'])
sds_dir = os.path.join(compass_dir, config['compass']['sds_dir'])
learning_tasks_dir = os.path.join(compass_dir,
                                  config['compass']['learning_tasks_dir'])
reports_dir = os.path.join(compass_dir, config['compass']['reports_dir'])
progress_reports_dir = os.path.join(compass_dir,
                                    config['compass']['progress_reports_dir'])
reports_csv = os.path.join(compass_dir, config['compass']['reports_csv'])
reports_summary_csv = os.path.join(compass_dir,
                                   config['compass']['reports_summary_csv'])
subjects_csv = os.path.join(compass_dir, config['compass']['subjects_csv'])
classes_csv = os.path.join(compass_dir, config['compass']['classes_csv'])
grade_dtype = pd.api.types.CategoricalDtype(
    categories=config['compass']['grade_order'], ordered=True)

# naplan
from vicedtools.naplan.dataservicesession import DataServiceBasicAuthenticator

dataservice_authenticator = DataServiceBasicAuthenticator(
    config['naplan']['username'], config['naplan']['password'])
naplan_dir = os.path.join(root_dir, config['naplan']['dir'])
naplan_outcomes_dir = os.path.join(naplan_dir, config['naplan']['outcomes_dir'])
naplan_sssr_dir = os.path.join(naplan_dir, config['naplan']['sssr_dir'])
naplan_outcomes_combined_csv = os.path.join(
    naplan_dir, config['naplan']['outcomes_combined_csv'])

# oars
oars_authenticator = OARSBasicAuthenticator(config['oars']['username'],
                                            config['oars']['password'])
oars_school_code = config['oars']['school_code']
oars_dir = os.path.join(root_dir, config['oars']['dir'])
pat_scores_csv = os.path.join(oars_dir, config['oars']['pat_scores_csv'])
pat_most_recent_csv = os.path.join(oars_dir,
                                   config['oars']['pat_most_recent_csv'])
ewrite_scores_csv = os.path.join(oars_dir, config['oars']['ewrite_scores_csv'])
ewrite_criteria_csv = os.path.join(oars_dir,
                                   config['oars']['ewrite_criteria_csv'])
pat_sittings_dir = os.path.join(oars_dir, config['oars']['pat_sittings_dir'])
ewrite_sittings_dir = os.path.join(oars_dir,
                                   config['oars']['ewrite_sittings_dir'])
oars_tests_json = os.path.join(oars_dir, config['oars']['oars_tests_json'])
scale_constructs_json = os.path.join(oars_dir,
                                     config['oars']['scale_constructs_json'])
oars_candidates_json = os.path.join(oars_dir,
                                    config['oars']['oars_candidates_json'])
oars_staff_xlsx = os.path.join(oars_dir, f"{oars_school_code}-staff.xlsx")

# gcp
gcp_project = config['gcp']['project']
general_dataset = config['gcp']['general_dataset']
vce_dataset = config['gcp']['vce_dataset']
student_details_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['student_details_table_id']}"
student_enrolments_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['student_enrolments_table_id']}"
pat_scores_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['pat_scores_table_id']}"
pat_most_recent_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['pat_most_recent_table_id']}"
naplan_outcomes_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['naplan_outcomes_table_id']}"
reports_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['reports_table_id']}"
reports_summary_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['reports_summary_table_id']}"
gat_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['gat_table_id']}"
ewrite_scores_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['ewrite_scores_table_id']}"
ewrite_criteria_table_id = f"{gcp_project}.{general_dataset}.{config['gcp']['general_dataset_tables']['ewrite_criteria_table_id']}"
vce_study_scores_table_id = f"{gcp_project}.{vce_dataset}.{config['gcp']['vce_dataset_tables']['vce_study_scores_table_id']}"
vce_adjusted_scores_table_id = f"{gcp_project}.{vce_dataset}.{config['gcp']['vce_dataset_tables']['vce_adjusted_scores_table_id']}"
gcs_bucket = config['gcp']['gcs_bucket']

# compass


def learning_task_filter(temp_df: pd.DataFrame) -> pd.DataFrame:
    temp_df = temp_df.loc[temp_df["IsIncludedInReport"], :]
    temp_df = temp_df.loc[(temp_df["ComponentType"] != "Comment"), :]
    temp_df = temp_df.loc[
        temp_df["ReportCycleName"].isin(["Semester One", "Semester Two"]), :]
    return temp_df


def class_code_parser(class_code, pattern_string):
    m = re.search(pattern_string, class_code)
    if m:
        subject_code = m.group('code')
        # test for Global Goodies vs Geography
        if subject_code == "10GG":
            m = re.search("10GGD[12345]", class_code)
            if m:
                subject_code = "10GL"
        return subject_code
    else:
        print(class_code + " not found")
        return ""
