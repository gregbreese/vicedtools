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
"""Functions for automating the exporting of data out of Compass."""

from __future__ import annotations

import os

from vicedtools.compass import CompassWebDriver, CompassDownloadFailedError


def export_all_reports(driver: CompassWebDriver,
                       root_dir: str,
                       learning_tasks_folder: str = "learning tasks",
                       reports_folder: str = "reports",
                       progress_reports_folder: str = "progress reports"):
    """Exports available reports data from Compass.
    
    Skips already downloaded data.
    
    Args:
        driver: An instance of CompassWebDriver
        root_dir: The root directory to download the reports into
        learning_tasks_folder: The sub-folder of the root directory to save
            learning tasks into.
        reports_folder: The sub-folder of the root directory to save reports
            exports into.
        progress_reports_folder: The sub-folder of the root directory to save
            progress reports exports into.
    """
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")

    learning_tasks_path = os.path.join(root_dir, learning_tasks_folder)
    reports_path = os.path.join(root_dir, reports_folder)
    progress_reports_path = os.path.join(root_dir, progress_reports_folder)

    paths = [learning_tasks_path, reports_path, progress_reports_path]
    for path in paths:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            os.mkdir(path)

    # learning task
    academic_years = driver.discover_academic_years()
    for academic_year in academic_years:
        if not os.path.exists(
                os.path.join(learning_tasks_path,
                             f"LearningTasks-{academic_year}.csv")):
            driver.export_learning_tasks(academic_year,
                                         download_path=learning_tasks_path)

    # reports
    report_cycles = driver.discover_report_cycles()
    for year, name in report_cycles:
        if not os.path.exists(
                os.path.join(reports_path,
                             f"SemesterReports-{year}-{name}.csv")):
            try:
                driver.export_report_cycle(year,
                                           name,
                                           download_path=reports_path)
            except CompassDownloadFailedError:
                print(f"Reports export failed for {year} {name}.")

    # progress reports
    progress_report_cycles = driver.discover_progress_report_cycles()
    for cycle in progress_report_cycles:
        if not os.path.exists(
                os.path.join(progress_reports_path, f"{cycle}.csv")):
            driver.export_progress_report(cycle,
                                          download_path=progress_reports_path)
