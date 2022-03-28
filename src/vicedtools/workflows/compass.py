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
from vicedtools.compass.reports import class_code_parser

from vicedtools.compass import (CompassWebDriver, CompassDownloadFailedError,
                                Reports, class_code_parser)
from vicedtools.gcp import (
    upload_csv_to_bigquery,
    STUDENT_DETAILS_SCHEMA,
    STUDENT_DETAILS_CLUSTERING_FIELDS,
    STUDENT_ENROLMENTS_SCHEMA,
    STUDENT_ENROLMENTS_CLUSTERING_FIELDS,
    REPORTS_SCHEMA,
    REPORTS_CLUSTERING_FIELDS,
    REPORTS_SUMMARY_SCHEMA,
    REPORTS_SUMMARY_CLUSTERING_FIELDS,
)


def export_students(
        driver: CompassWebDriver,
        root_dir: str,
        student_details_folder: str = "student details",
        student_details_file: str = "student details.csv",
        student_class_relationships_folder: str = "student class relationships"
):
    """Exports available student details and class data from Compass.
       
    Args:
        driver: An instance of CompassWebDriver
        root_dir: The root directory to download the reports into
        student_details_folder: The sub-folder of the root directory to save
            student details into.
        student_class_relationships_folder: The sub-folder of the root directory to save 
            class relationships data into.
    """
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")

    student_details_path = os.path.join(root_dir, student_details_folder)
    student_class_relationships_path = os.path.join(
        root_dir, student_class_relationships_folder)

    paths = [student_details_path, student_class_relationships_path]
    for path in paths:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            os.mkdir(path)

    # student details
    student_details_file = os.path.join(student_details_path,
                                        student_details_file)
    driver.export_student_details(student_details_file, detailed=True)

    # student class relationships
    driver.export_sds(student_class_relationships_path)


def upload_students_to_bq(
        student_details_table_id: str,
        student_class_relationships_table_id: str,
        bucket: str,
        root_dir: str,
        student_details_folder: str = "student details",
        student_details_file: str = "student details.csv",
        student_class_relationships_folder: str = "student class relationships"
):
    """Uploads student details and class data to BigQuery.
    
    Designed to integrate with vicedtools.automation.compass.export_students(),
    but will also work fine with manually downloaded files.

    Args:
        student_details_table_id: The BigQuery table id to upload the student 
            details table to
        student_class_relationships_table_id: The BigQuery table id to upload 
            the student-class relationship table to
        bucket: The GSC bucket to use for temporary storage. Must be in the
            same region as the BQ tables are hosted.
        root_dir: The root folder where the student details data is stored.
        student_details_folder: The sub-folder of the root_dir where the
            student details file is stored.
        student_details_file: The name of the student details csv file.
        student_class_relationships_folder: The sub-folder of the root_dir
            where the SDS export has been downloaded and expanded into.
    """
    # student details
    student_details_file = os.path.join(root_dir, student_details_folder,
                                        student_details_file)
    temp_file = os.path.join(root_dir, student_details_folder, "temp.csv")

    details_df = pd.read_csv(student_details_file,
                             keep_default_na=False,
                             dtype=str)
    details_df = details_df[details_df["Status"].isin(["Active",
                                                       "Left"])].copy()
    details_df.rename(columns={
        "SUSSI ID": "StudentCode",
        "First Name": "FirstName",
        "Preferred Name": "PrefName",
        "Last Name": "Surname",
        "Year Level": "YearLevel",
        "Form Group": "HomeGroup",
        "Date of birth": "DateOfBirth"
    },
                      inplace=True)

    details_df["Surname"] = details_df["Surname"].str.title()
    details_df["FirstName"] = details_df["FirstName"].str.title()
    details_df["PrefName"] = details_df["PrefName"].str.title()

    details_df["DateOfBirth"] = pd.to_datetime(details_df["DateOfBirth"],
                                               format="%d/%m/%Y")

    def year_level_number(yr_lvl_str):
        if yr_lvl_str:
            digits = yr_lvl_str[-2:]
            return int(digits)
        else:
            return ""

    details_df["YearLevel"] = details_df["YearLevel"].apply(year_level_number)

    columns = [
        "StudentCode", "Surname", "FirstName", "PrefName", "Gender",
        "YearLevel", "HomeGroup", "Status", "DateOfBirth"
    ]
    details_df[columns].to_csv(temp_file, index=False)

    upload_csv_to_bigquery(temp_file, STUDENT_DETAILS_SCHEMA,
                           STUDENT_DETAILS_CLUSTERING_FIELDS,
                           student_details_table_id, bucket)
    os.remove(temp_file)

    # student class relationships
    student_class_relationships_file = os.path.join(
        root_dir, student_class_relationships_folder, "StudentEnrollment.csv")
    temp_file = os.path.join(root_dir, student_class_relationships_folder,
                             "temp.csv")

    student_enrollment_df = pd.read_csv(student_class_relationships_file)
    student_enrollment_df.rename(columns={
        "SIS ID": "StudentCode",
    },
                                 inplace=True)

    student_enrollment_df[[
        'ClassGroupCode', 'Cycle'
    ]] = student_enrollment_df['Section SIS ID'].str.split('-', expand=True)
    columns = ["ClassGroupCode", "StudentCode"]
    student_enrollment_df[columns].to_csv(temp_file, index=False)

    upload_csv_to_bigquery(temp_file, STUDENT_ENROLMENTS_SCHEMA,
                           STUDENT_ENROLMENTS_CLUSTERING_FIELDS,
                           student_class_relationships_table_id, bucket)
    os.remove(temp_file)


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


def upload_reports_to_bq(
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

    learning_task_files = os.path.join(root_dir, learning_tasks_folder, "*.csv")
    reports_files = os.path.join(root_dir, reports_folder, "*.csv")
    progress_reports_files = os.path.join(root_dir, progress_reports_folder,
                                          "*.csv")

    files = glob.glob(learning_task_files)
    for filename in files:
        print("importing ", filename)
        reports.addLearningTasksExport(
            filename,
            grade_dtype=results_dtype,
            replace_values=replace_values,
            grade_score_mapper=learning_tasks_result_mapper)

    files = glob.glob(reports_files)
    for filename in files:
        print("importing ", filename)
        reports.addReportsExport(filename,
                                 grade_dtype=results_dtype,
                                 replace_values=replace_values,
                                 grade_score_mapper=work_habits_result_mapper)

    files = glob.glob(progress_reports_files)
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

    upload_csv_to_bigquery(reports_file, REPORTS_SCHEMA,
                           REPORTS_CLUSTERING_FIELDS, reports_table_id, bucket)
    upload_csv_to_bigquery(summary_file, REPORTS_SUMMARY_SCHEMA,
                           REPORTS_SUMMARY_CLUSTERING_FIELDS,
                           reports_summary_table_id, bucket)
