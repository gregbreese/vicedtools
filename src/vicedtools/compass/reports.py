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
"""A class for storing reporting data exported from Compass.

Aggregates data from Learning Tasks, Reports and Progress reports exports.
"""
from __future__ import annotations

import re
from typing import Callable

import pandas as pd
from pandas.errors import EmptyDataError


def class_code_parser(class_code: str, pattern: str) -> str:
    """A default class code to subject code parser.

    Assumes that class codes contain their corresponding subject code.
    
    Args:
        class_code: The class code.
        pattern: A regex pattern that matches subject codes to a named group
            called 'code'.

    Returns:
        The subject code string.
    """
    m = re.search(pattern, class_code)
    if m:
        subject_code = m.group('code')
        return subject_code
    else:
        print(class_code + " class code not found")
        return ""


class Reports:
    '''A container class for reporting data from Compass.'''

    def __init__(self, data=None, class_details=None) -> Reports:
        columns = [
            'Time', 'ClassCode', 'StudentCode', 'ResultName', 'ResultGrade',
            'ResultScore', 'Type', 'SubjectCode', 'SubjectName', 'LearningArea',
            'TeacherCode'
        ]
        self.data = pd.DataFrame(columns=columns)
        if type(data) == pd.core.frame.DataFrame:
            self.data = pd.concat([self.data, data], ignore_index=True)
        columns = ['Time', 'ClassCode', 'TeacherCode']
        self.class_details = pd.DataFrame(columns=columns).dropna(
            subset=["TeacherCode"])
        if type(class_details) == pd.core.frame.DataFrame:
            self.class_details = pd.concat([
                self.class_details,
                class_details.dropna(subset=["TeacherCode"])
            ],
                                           ignore_index=True)

    @classmethod
    def fromReportsExport(cls,
                          filename: str,
                          year: str = None,
                          semester: str = None,
                          grade_score_mapper: dict[str, float] = None,
                          grade_dtype: pd.api.types.CategoricalDtype = None,
                          replace_values: dict[str, dict] = None) -> Reports:
        """Creates a new Reports instance from a Compass reports export."""
        try:
            temp_df = pd.read_csv(filename,
                                  na_values=None,
                                  keep_default_na=False)
        except EmptyDataError:
            return Reports()
        temp_df = temp_df.loc[(temp_df["AssessmentType"] == "Work Habits"), :]

        if not year:
            # attempt to determine year from filename
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern, filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError(
                    "Could not determine year for reports export file.]n"
                    "Try including the year in the filename.")
        if not semester:
            semester_pattern = "(?:[Ss][Ee][Mm][A-Za-z ]*)(?P<semester>[12]|[Oo]ne|[Tt]wo)"
            m = re.search(semester_pattern, filename)
            if m:
                semester = m.group('semester')
            else:
                raise ValueError(
                    "Could not determine semester for reports export file.\n"
                    "Try including Sem 1, Sem 2 in the filenames.")
        time = cls._semester_date_mapper(year, semester)
        temp_df["Time"] = time
        temp_df["Time"] = pd.to_datetime(temp_df["Time"])

        if replace_values:
            temp_df.replace(replace_values, inplace=True)
        if grade_dtype:
            temp_df["Result"] = temp_df["Result"].astype(grade_dtype)
            temp_df.dropna(subset=["Result"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["Result"].map(grade_score_mapper)
        else:
            temp_df["ResultScore"] = None

        temp_df.rename(columns={
            "Result": "ResultGrade",
            "AssessmentArea": "ResultName",
            "AssessmentType": "Type"
        },
                       inplace=True)

        temp_df["SubjectName"] = None
        temp_df["TeacherCode"] = None

        columns = [
            'Time', 'ClassCode', 'StudentCode', 'ResultName', 'ResultGrade',
            'ResultScore', 'Type', 'SubjectName', 'TeacherCode'
        ]
        return cls(temp_df[columns])

    @classmethod
    def fromLearningTasksExport(
            cls,
            filename: str,
            year: str = None,
            grade_score_mapper: dict[str, float] = None,
            grade_dtype: pd.api.types.CategoricalDtype = None,
            learning_task_filter: Callable[[pd.DataFrame], pd.DataFrame] = None,
            replace_values: dict[str, dict] = None) -> Reports:
        """Creates a new Reports instance from a Compass Learning Tasks export."""
        try:
            temp_df = pd.read_csv(filename,
                                  na_values=None,
                                  keep_default_na=False)
        except EmptyDataError:
            return Reports()

        if learning_task_filter:
            temp_df = learning_task_filter(temp_df)

        if (not year):
            # attempt to determine year from filename
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern, filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError(
                    "Could not determine year for Learning Tasks export file.")
        temp_df["Year"] = year
        temp_df["Time"] = temp_df.apply(lambda x: cls._semester_date_mapper(
            x["Year"], x["ReportCycleName"]),
                                        axis=1,
                                        result_type='reduce')
        temp_df['Time'] = pd.to_datetime(temp_df['Time'])

        temp_df["Type"] = "Academic"  # differentiate from work habits

        if replace_values:
            temp_df.replace(replace_values, inplace=True)
        if grade_dtype:
            temp_df["Result"] = temp_df["Result"].astype(grade_dtype)
            temp_df.dropna(subset=["Result"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["Result"].map(grade_score_mapper)
        else:
            temp_df["ResultScore"] = None
        temp_df.rename(columns={
            'Code': 'ClassCode',
            'TaskName': 'ResultName',
            'Result': 'ResultGrade',
            "TeacherImportIdentifier": "TeacherCode"
        },
                       inplace=True)
        class_details_columns = ['Time', 'ClassCode', 'TeacherCode']
        data_columns = [
            'Time', 'ClassCode', 'StudentCode', 'ResultName', 'ResultGrade',
            'ResultScore', 'Type', 'SubjectName', 'TeacherCode'
        ]
        return cls(temp_df[data_columns], temp_df[class_details_columns])

    @classmethod
    def fromProgressReportsExport(
            cls,
            filename: str,
            progress_report_items: list[str],
            year: str = None,
            term: str = None,
            grade_score_mapper: dict[str, float] = None,
            grade_dtype: pd.api.types.CategoricalDtype = None,
            replace_values: dict[str, dict] = None) -> Reports:
        """Creates a new Reports instance from a Compass progress reports export."""
        try:
            temp_df = pd.read_csv(filename,
                                  na_values=None,
                                  keep_default_na=False)
        except EmptyDataError:
            return Reports()
        temp_df.rename(columns={
            "Id": "StudentCode",
            "Subject": "ClassCode",
            "Teacher": "TeacherCode"
        },
                       inplace=True)

        # unpivot progress report items
        temp_df = temp_df.melt(
            id_vars=["StudentCode", "ClassCode", "TeacherCode"],
            value_vars=[
                x for x in progress_report_items if x in temp_df.columns
            ],
            var_name="ResultName",
            value_name="ResultGrade")

        if not year:
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern, filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError("Could not determine year from filename.")
        if not term:
            term_pattern = "(?:[Tt][Ee][Rr][A-Za-z ]*)(?P<term>[1234])"
            m = re.search(term_pattern, filename)
            if m:
                term = m.group('term')
            else:
                raise ValueError("Could not determine term from filename.")
        time = cls._termDateMapper(year, term)
        temp_df["Time"] = time
        temp_df['Time'] = pd.to_datetime(temp_df['Time'])

        temp_df["Type"] = "Work Habits"

        if replace_values:
            temp_df.replace(replace_values, inplace=True)
        if grade_dtype:
            temp_df["ResultGrade"] = temp_df["ResultGrade"].astype(grade_dtype)
            temp_df.dropna(subset=["ResultGrade"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["ResultGrade"].map(
                grade_score_mapper)
        else:
            temp_df["ResultScore"] = None

        temp_df["SubjectName"] = None

        class_details_columns = ['Time', 'ClassCode', 'TeacherCode']
        data_columns = [
            'Time', 'ClassCode', 'StudentCode', 'ResultName', 'ResultGrade',
            'ResultScore', 'Type', 'SubjectName', 'TeacherCode'
        ]
        return cls(temp_df[data_columns], temp_df[class_details_columns])

    @classmethod
    def _semester_date_mapper(cls, year: str, semester: str) -> str:
        # remove year-like strings from semester
        semester = re.sub("[0-9]{4}", "", semester)
        # try to identify semester
        sem_one_pattern = "1|[Oo]ne"
        sem_two_pattern = "2|[Tt]wo"
        m = re.search(sem_one_pattern, semester)
        if m:
            return str(year) + "-06-30"
        m = re.search(sem_two_pattern, semester)
        if m:
            return str(year) + "-12-31"
        return str(year) + "-12-31"

    @classmethod
    def _termDateMapper(cls, year: str, term: str) -> str:
        if term in ["1", "One", "one"]:
            return str(year) + "-03-31"
        elif term in ["2", "Two", "two"]:
            return str(year) + "-06-30"
        elif term in ["3", "Three", "three"]:
            return str(year) + "-09-30"
        elif term in ["4", "Four", "four"]:
            return str(year) + "-12-31"
        else:
            return None

    def addLearningTasksExport(
            self,
            filename: str,
            grade_score_mapper: dict[str, float] = None,
            grade_dtype: pd.api.types.CategoricalDtype = None,
            learning_task_filter: Callable[[pd.DataFrame], pd.DataFrame] = None,
            replace_values: dict[str, dict] = None) -> None:
        """Adds data from a Compass Learning Tasks export."""

        temp = Reports.fromLearningTasksExport(
            filename,
            grade_score_mapper=grade_score_mapper,
            grade_dtype=grade_dtype,
            learning_task_filter=learning_task_filter,
            replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data], ignore_index=True)
        self.data.drop_duplicates(
            subset=["Time", "StudentCode", "ClassCode", "ResultName"],
            inplace=True)
        self.class_details = pd.concat([
            self.class_details,
            temp.class_details.dropna(subset=["TeacherCode"])
        ],
                                       ignore_index=True)
        self.class_details.drop_duplicates(inplace=True)

    def addReportsExport(self,
                         filename: str,
                         grade_score_mapper: dict[str, float] = None,
                         grade_dtype: pd.api.types.CategoricalDtype = None,
                         replace_values: dict[str, dict] = None) -> None:
        """Adds data from a Compass reports export."""

        temp = Reports.fromReportsExport(filename,
                                         grade_score_mapper=grade_score_mapper,
                                         grade_dtype=grade_dtype,
                                         replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data], ignore_index=True)
        self.data.drop_duplicates(
            subset=["Time", "StudentCode", "ClassCode", "ResultName"],
            inplace=True)

    def addProgressReportsExport(
            self,
            filename: str,
            progress_report_items: list[str],
            grade_score_mapper: dict[str, float] = None,
            grade_dtype: pd.api.types.CategoricalDtype = None,
            replace_values: dict[str, dict] = None) -> None:
        """Adds data from a Compass progress reports export."""

        temp = Reports.fromProgressReportsExport(
            filename,
            progress_report_items,
            grade_score_mapper=grade_score_mapper,
            grade_dtype=grade_dtype,
            replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data], ignore_index=True)
        self.data.drop_duplicates(
            subset=["Time", "StudentCode", "ClassCode", "ResultName"],
            inplace=True)
        self.class_details = pd.concat([
            self.class_details,
            temp.class_details.dropna(subset=["TeacherCode"])
        ],
                                       ignore_index=True)
        self.class_details.drop_duplicates(inplace=True)

    def __add__(self, other: Reports):
        data = pd.concat([self.data, other.data], ignore_index=True)
        data.drop_duplicates(
            subset=["Time", "StudentCode", "ClassCode", "ResultName"],
            inplace=True)
        return Reports(data)

    def importSubjectsData(self,
                           classes_csv: str,
                           replace_values: dict[str, dict] = None) -> None:
        """Adds subject metadata from a separate csv file.
        
        Imports subject codes and names from the Compass classes csv export.

        Args:
            classes_csv: The path to the classes csv file.
            replace_values: A dictionary to be passed to DataFrame.replace().
                Keys are columns and values are dictionaries containing 
                remappings for values in that column. Can be used to
                standardise things where your school has changed the name of a
                subject or learning area over time.
        """

        classes_df = pd.read_csv(classes_csv)

        self.data["Year"] = self.data["Time"].dt.year
        reports_columns = [
            'Time',
            'ClassCode',
            'StudentCode',
            'ResultName',
            'ResultGrade',
            'ResultScore',
            'Type',
            'Year',
        ]
        classes_columns = [
            'LearningArea', 'ClassCode', 'SubjectCode', 'SubjectName',
            'TeacherCode', 'Year'
        ]
        self.data = pd.merge(self.data[reports_columns],
                             classes_df[classes_columns],
                             how="left",
                             on=["ClassCode", "Year"])
        if replace_values:
            self.data.replace(replace_values, inplace=True)
        self.data.drop(columns="Year", inplace=True)
        # Force learning area names to all caps
        self.data['LearningArea'] = self.data['LearningArea'].str.upper()

    def updateFromClassDetails(self) -> None:
        """Infills TeacherCode data with data available from other reports."""

        self.data.drop(columns="TeacherCode", inplace=True, errors="ignore")
        self.data = pd.merge(self.data,
                             self.class_details,
                             how="left",
                             on=["Time", "ClassCode"])

    def summary(self) -> pd.DataFrame:
        """Aggregates Academic and Work Habits results to produce a summary."""
        columns = [
            'Time', 'ClassCode', 'StudentCode', 'ResultScore', 'Type',
            'LearningArea', 'SubjectCode', 'SubjectName', 'TeacherCode'
        ]
        grpd = self.data[columns].groupby([
            'Time', 'ClassCode', 'StudentCode', 'Type', 'SubjectCode',
            'SubjectName', 'LearningArea', 'TeacherCode'
        ],
                                          as_index=False).mean()
        pvtd = grpd.pivot_table(index=[
            'Time', 'ClassCode', 'StudentCode', 'SubjectCode', 'SubjectName',
            'LearningArea', 'TeacherCode'
        ],
                                columns=["Type"],
                                values="ResultScore").reset_index()
        pvtd.sort_values("Time", ascending=False, inplace=True)
        return pvtd

    def saveReports(self, filename: str) -> None:
        self.data.to_csv(filename, index=False)

    def saveSummary(self, filename: str) -> None:
        summary = self.summary()
        summary.to_csv(filename, index=False)
