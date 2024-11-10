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
from vicedtools.scripts.config import (
    config, learning_tasks_dir, progress_reports_dir, reports_dir,
    compass_progress_reports_schema, compass_learning_tasks_schema,
    compass_reports_schema, enrolments_csv, classes_csv, reports_csv,
    reports_summary_csv)


def main():
    reports = Reports(classes_csv, enrolments_csv)

    # import learning task data
    files = glob.glob(os.path.join(learning_tasks_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addLearningTasksExport(
                filename,
                compass_learning_tasks_schema,
                replace_values=config['compass']['replace_values'])
        except ValueError:
            pass

    # import report data
    files = glob.glob(os.path.join(reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addReportsExport(
                filename,
                compass_reports_schema,
                replace_values=config['compass']['replace_values'])
        except ValueError:
            pass

    # import progress report data
    files = glob.glob(os.path.join(progress_reports_dir, "*.csv"))
    for filename in files:
        print("importing ", filename)
        try:
            reports.addProgressReportsExport(
                filename,
                compass_progress_reports_schema,
                replace_values=config['compass']['replace_values'])
        except ValueError:
            pass

    reports.saveReports(reports_csv)
    reports.saveSummary(reports_summary_csv)


if __name__ == "__main__":
    main()
