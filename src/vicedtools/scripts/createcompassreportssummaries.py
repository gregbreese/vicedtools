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
"""Executable script for creating summaries of all Compass student results."""

import glob
import os

from vicedtools.compass import Reports
from vicedtools.scripts._config import (config, learning_tasks_dir,
                                        progress_reports_dir, reports_dir,
                                        learning_task_filter, grade_dtype,
                                        classes_csv, reports_csv, 
                                        reports_summary_csv)


def main():
    reports = Reports()

    files = glob.glob(os.path.join(learning_tasks_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addLearningTasksExport(
                filename,
                grade_dtype=grade_dtype,
                replace_values=config['compass']['replace_values'],
                grade_score_mapper=config['compass']['learning_tasks']
                ['result_values'],
                learning_task_filter=learning_task_filter)
        except ValueError:
            pass

    files = glob.glob(os.path.join(reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addReportsExport(
                filename,
                grade_dtype=grade_dtype,
                replace_values=config['compass']['replace_values'],
                grade_score_mapper=config['compass']['reports']
                ['result_values'])
        except ValueError:
            pass
    files = glob.glob(os.path.join(progress_reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addProgressReportsExport(
                filename,
                config['compass']['progress_reports']['progress_report_items'],
                grade_dtype=grade_dtype,
                grade_score_mapper=config['compass']['progress_reports']
                ['result_values'])
        except ValueError:
            pass
    reports.importSubjectsData(
        classes_csv,
        replace_values=config['compass']['replace_values'])

    reports.saveReports(reports_csv)
    reports.saveSummary(reports_summary_csv)


if __name__ == "__main__":
    main()
