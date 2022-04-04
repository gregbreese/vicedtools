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
"""Executable script for exporting Compass progress report data."""

import glob
import os

import pandas as pd
from vicedtools.compass import Reports

if __name__ == "__main__":
    from config import (root_dir, compass_folder, progress_reports_folder,
                        learning_tasks_folder, reports_folder, replace_values,
                        replace_subject_codes, work_habits_result_mapper,
                        learning_tasks_result_mapper,
                        progress_report_result_mapper, results_dtype,
                        progress_report_items, gwsc_class_code_parser,
                        subjects_file, reports_csv, reports_summary_csv)

    compass_dir = os.path.join(root_dir, compass_folder)
    progress_reports_dir = os.path.join(compass_dir, progress_reports_folder)
    learning_tasks_dir = os.path.join(compass_dir, learning_tasks_folder)
    reports_dir = os.path.join(compass_dir, reports_folder)

    reports = Reports()

    files = glob.glob(os.path.join(learning_tasks_dir, "*.csv"))
    df = pd.DataFrame()
    for filename in files:
        print("importing ", filename)
        reports.addLearningTasksExport(
            filename,
            grade_dtype=results_dtype,
            replace_values=replace_values,
            grade_score_mapper=learning_tasks_result_mapper)

    files = glob.glob(os.path.join(reports_dir, "*.csv"))
    df = pd.DataFrame()
    for filename in files:
        print("importing ", filename)
        reports.addReportsExport(filename,
                                 grade_dtype=results_dtype,
                                 replace_values=replace_values,
                                 grade_score_mapper=work_habits_result_mapper)

    files = glob.glob(os.path.join(progress_reports_dir, "*.csv"))

    progress_reports_df = pd.DataFrame()
    for filename in files:
        print("importing ", filename)
        reports.addProgressReportsExport(
            filename,
            progress_report_items,
            grade_dtype=results_dtype,
            grade_score_mapper=progress_report_result_mapper)

    reports.importSubjectsData(subjects_file,
                               gwsc_class_code_parser,
                               replace_values=replace_subject_codes)

    reports.updateFromClassDetails()

    reports_file = os.path.join(compass_dir, reports_csv)
    summary_file = os.path.join(compass_dir, reports_summary_csv)
    reports.saveReports(reports_file)
    reports.saveSummary(summary_file)
