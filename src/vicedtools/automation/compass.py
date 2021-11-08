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

import glob
from typing import Callable
import os

import pandas as pd
from compass.reports import class_code_parser

from vicedtools.compass import (CompassWebDriver, CompassDownloadFailedError,
                                Reports, class_code_parser)
from vicedtools.automation.gcp import (upload_to_bigquery, REPORTS_SCHEMA,
                                       REPORTS_CLUSTERING_FIELDS,
                                       REPORTS_SUMMARY_SCHEMA,
                                       REPORTS_SUMMARY_CLUSTERING_FIELDS)


def export_reports(driver: CompassWebDriver,
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


def upload_reports_to_gcp(
    reports_table_id: str,
    reports_summary_table_id: str,
    bucket: str,
    root_dir: str,
    subjects_file: str,
    work_habits_result_mapper: Callable[[str], float],
    learning_tasks_result_mapper: Callable[[str], float],
    progress_report_result_mapper: Callable[[str], float],
    results_dtype: pd.api.types.CategoricalDtype,
    progress_report_items: list[str],
    learning_tasks_folder: str = "learning tasks",
    reports_folder: str = "reports",
    progress_reports_folder: str = "progress reports",
    replace_values={},
    class_code_parser=class_code_parser,
):
    """Combines all report data and uploads to a BigQuery table.
    
    Discovers reports data in the given folders and consolidates them. Saves
    two csv files, a full data set with a row for each item and a summary with
    a row for each subject per semester.

    Args:
        reports_table_id: The BigQuery table id to upload the reports table to.
        reports_summary_table_id: The BigQuery table id to upload the reports
            summary table to.
        bucket: The GSC bucket to use for temporary storage.
        root_dir: The root folder where reports data is stored. Assumes that
            the learning tasks, reports and progress reports data is stored
            in subfolders. The reports.csv and reports_summary.csv files will
            be saved in this location.
        subjects_file: A csv file containg the subject metadata for the school.
            Expects a csv with columns 'SubjectCode', 'LearningArea', 
            'SubjectName'.
        work_habits_results_mapper: A function that maps your school's work
            habits grade names to a scale on the interval [0,1].
        learning_tasks_results_mapper: A function that maps your school's
            learning tasks grade names to a scale on the interval [0,1].
        progress_reports_results_mapper: A function that maps your school's
            progress report grade names to a scale on the interval [0,1].
        progress_report_items: A list of the names of your school's progress
            report items.
    """

    reports = Reports()

    learning_task_dir = os.path.join(root_dir, learning_tasks_folder)
    reports_dir = os.path.join(root_dir, reports_folder)
    progress_reports_dir = os.path.join(root_dir, progress_reports_folder)

    files = glob.glob(learning_task_dir + "*.csv")
    for filename in files:
        print("importing ", filename)
        reports.addLearningTasksExport(
            filename,
            grade_dtype=results_dtype,
            replace_values=replace_values,
            grade_score_mapper=learning_tasks_result_mapper)

    files = glob.glob(reports_dir + "*.csv")
    for filename in files:
        print("importing ", filename)
        reports.addReportsExport(filename,
                                 grade_dtype=results_dtype,
                                 replace_values=replace_values,
                                 grade_score_mapper=work_habits_result_mapper)

    files = glob.glob(progress_reports_dir + "*.csv")
    for filename in files:
        print("importing ", filename)
        reports.addProgressReportsExport(
            filename,
            progress_report_items,
            grade_dtype=results_dtype,
            grade_score_mapper=progress_report_result_mapper)

    reports.importSubjectsData(subjects_file,
                               class_code_parser,
                               replace_values=replace_values)

    reports.updateFromClassDetails()

    reports_file = os.path.join(root_dir, "reports.csv")
    summary_file = os.path.join(root_dir, "reports_summary.csv")

    reports.saveReports(reports_file)
    reports.saveSummary(summary_file)

    upload_to_bigquery(reports_file, REPORTS_SCHEMA, REPORTS_CLUSTERING_FIELDS,
                       reports_table_id, bucket)
    upload_to_bigquery(summary_file, REPORTS_SUMMARY_SCHEMA,
                       REPORTS_SUMMARY_CLUSTERING_FIELDS,
                       reports_summary_table_id, bucket)
