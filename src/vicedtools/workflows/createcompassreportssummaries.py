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
"""Executable script for creating summaries of all Compass student results."""

import glob
import os

from vicedtools.compass import Reports

if __name__ == "__main__":
    from config import (learning_tasks_dir, progress_reports_dir, reports_dir,
                        replace_values, replace_subject_codes,
                        work_habits_result_mapper, learning_task_filter,
                        learning_tasks_result_mapper,
                        progress_report_result_mapper, results_dtype,
                        progress_report_items, class_code_parser,
                        subjects_metadata_csv, reports_csv, reports_summary_csv)

    reports = Reports()

    files = glob.glob(os.path.join(learning_tasks_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addLearningTasksExport(
                filename,
                grade_dtype=results_dtype,
                replace_values=replace_values,
                grade_score_mapper=learning_tasks_result_mapper,
                learning_task_filter=learning_task_filter)
        except ValueError:
            pass

    files = glob.glob(os.path.join(reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addReportsExport(
                filename,
                grade_dtype=results_dtype,
                replace_values=replace_values,
                grade_score_mapper=work_habits_result_mapper)
        except ValueError:
            pass
    files = glob.glob(os.path.join(progress_reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addProgressReportsExport(
                filename,
                progress_report_items,
                grade_dtype=results_dtype,
                grade_score_mapper=progress_report_result_mapper)
        except ValueError:
            pass
    reports.importSubjectsData(subjects_metadata_csv,
                               class_code_parser,
                               replace_values=replace_subject_codes)

    reports.updateFromClassDetails()

    reports.saveReports(reports_csv)
    reports.saveSummary(reports_summary_csv)
