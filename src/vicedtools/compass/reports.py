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

import pandas as pd
from pandas.errors import EmptyDataError


class Reports:
    '''A container class for reporting data from Compass.'''

    def __init__(self,
                 classes_csv: str,
                 enrolments_csv: str,
                 data: pd.DataFrame = None) -> Reports:
        columns = [
            'Time', 'LearningArea', 'SubjectCode', 'ClassCode', "TeacherCode",
            'StudentCode', 'ResultName', 'ResultGrade', 'ResultScore', 'Type'
        ]
        if type(data) == pd.core.frame.DataFrame:
            self.data = data[columns]
        else:
            self.data = pd.DataFrame(columns=columns)
        self.classes = pd.read_csv(classes_csv)
        self.enrolments = pd.read_csv(enrolments_csv)

    @classmethod
    def date_from_filename(cls, filename: str) -> str:
        # attempt to determine year from filename
        year_pattern = "(?P<year>2[0-9][0-9][0-9])"
        semester_pattern = "(?:[Ss][Ee][Mm][A-Za-z ]*)(?P<semester>[12]|[Oo]ne|[Tt]wo)"
        term_pattern = "(?:[Tt][Ee][Rr][A-Za-z ]*)(?P<term>[1234]|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]our)"
        m = re.search(year_pattern, filename)
        if m:
            year = m.group('year')
        else:
            raise ValueError(
                "Could not determine year for reports export file.\n"
                "Try including the year in the filename.")
        m = re.search(semester_pattern, filename)
        if m:
            # matched semester
            # check for interim/progress/mid-semester
            semester = m.group('semester')
            interim_pattern = "[Ii]nterim|[Pp]rogress|[Mm]id"
            m = re.search(interim_pattern, filename)
            if m:
                interim = True
            else:
                interim = False
            sem_one_pattern = "1|[Oo]ne"
            sem_two_pattern = "2|[Tt]wo"
            m = re.search(sem_one_pattern, semester)
            if m:
                if interim:
                    term = 1
                else:
                    term = 2
            m = re.search(sem_two_pattern, semester)
            if m:
                if interim:
                    term = 3
                else:
                    term = 4
        else:
            m = re.search(term_pattern, filename)
            if m:
                # matched term
                if term in ["1", "One", "one"]:
                    term = 1
                elif term in ["2", "Two", "two"]:
                    term = 2
                elif term in ["3", "Three", "three"]:
                    term = 3
                elif term in ["4", "Four", "four"]:
                    term = 4
            else:
                # no semester or term matches found
                term = 4
        if term == 1:
            return str(year) + "-03-31"
        elif term == 2:
            return str(year) + "-06-30"
        elif term == 3:
            return str(year) + "-09-30"
        elif term == 4:
            return str(year) + "-12-31"

    def addLearningTasksExport(self,
                               filename: str,
                               compass_learning_tasks_schema: list[dict],
                               replace_values: dict[str, dict] = None,
                               year: str = None) -> None:
        """Adds data from a Compass Learning Tasks export."""
        temp_df = pd.read_csv(filename,
                              na_values=None,
                              keep_default_na=False,
                              dtype=str)

        if (not year):
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern, filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError(
                    "Could not determine year for reports export file.\n"
                    "Try including the year in the filename.")
        temp_df['Year'] = int(year)

        subject_wide_rows = temp_df['IsSubjectWide'] == "True"

        subject_tasks = temp_df.loc[subject_wide_rows].merge(
            self.enrolments[[
                "Year", "ClassCode", "SubjectCode", "LearningArea",
                "StudentCode"
            ]],
            left_on=['Code', 'StudentCode', 'Year'],
            right_on=['SubjectCode', 'StudentCode', 'Year'],
            how='left')
        class_tasks = temp_df.loc[~subject_wide_rows].merge(
            self.enrolments[[
                "Year", "ClassCode", "SubjectCode", "LearningArea",
                "StudentCode"
            ]],
            left_on=['Code', 'StudentCode', 'Year'],
            right_on=['ClassCode', 'StudentCode', 'Year'],
            how='left')

        temp_df = pd.concat([subject_tasks, class_tasks])

        for data_set in compass_learning_tasks_schema:
            row_sets = []
            for filter in data_set['filters']:
                rows = temp_df[filter['column']] == filter['value']
                row_sets.append(rows)
            rows = pd.concat(row_sets, axis=1).all(axis=1)
            selected_df = temp_df.loc[rows].copy()
            if len(selected_df) == 0:
                continue
            selected_df["Time"] = f"{year}{data_set['time_suffix']}"
            selected_df["Type"] = data_set['type']
            if replace_values:
                selected_df.replace(replace_values, inplace=True)
            results = selected_df["Result"].unique()
            for result in results:
                if result not in data_set['result_values'].keys():
                    print(
                        f"Warning: Result '{result}' not found in result_values mapping for data_set {data_set['filters']}."
                    )
            selected_df["ResultScore"] = selected_df["Result"].map(
                data_set['result_values'])
            selected_df.rename(columns={
                "Result": "ResultGrade",
                "TaskName": "ResultName",
            },
                               inplace=True)
            selected_df = selected_df.merge(
                self.classes[["Year", "ClassCode", "TeacherCode"]],
                on=["Year", "ClassCode"],
                how='left')
            columns = [
                'Time', 'LearningArea', 'SubjectCode', 'ClassCode',
                "TeacherCode", 'StudentCode', 'ResultName', 'ResultGrade',
                'ResultScore', 'Type'
            ]
            self.data = pd.concat([self.data, selected_df[columns]],
                                  ignore_index=True)

    def addReportsExport(
        self,
        filename: str,
        compass_reports_schema: list[dict],
        replace_values: dict[str, dict] = None,
        time=None,
    ) -> None:
        """Adds data from a Compass reports export."""
        try:
            temp_df = pd.read_csv(filename,
                                  na_values=None,
                                  keep_default_na=False,
                                  dtype=str)
        except EmptyDataError:
            return Reports()

        if (not time):
            time = Reports.date_from_filename(filename)
        temp_df["Time"] = time
        temp_df["Time"] = pd.to_datetime(temp_df["Time"])

        for data_set in compass_reports_schema:
            row_sets = []
            for filter in data_set['filters']:
                rows = temp_df[filter['column']] == filter['value']
                row_sets.append(rows)
            rows = pd.concat(row_sets, axis=1).all(axis=1)
            selected_df = temp_df.loc[rows].copy()
            if len(selected_df) == 0:
                continue
            selected_df["Type"] = data_set['type']
            if replace_values:
                selected_df.replace(replace_values, inplace=True)

            results = selected_df["Result"].unique()
            for result in results:
                if result not in data_set['result_values'].keys():
                    print(
                        f"Warning: Result '{result}' not found in result_values mapping for data_set {data_set['filters']}."
                    )
            selected_df["ResultScore"] = selected_df["Result"].map(
                data_set['result_values'])
            selected_df.rename(columns={
                "Result": "ResultGrade",
                "AssessmentArea": "ResultName",
            },
                               inplace=True)

            selected_df['Year'] = selected_df['Time'].dt.year
            selected_df = selected_df.merge(self.classes[[
                "Year", "ClassCode", "SubjectCode", "LearningArea",
                "TeacherCode"
            ]],
                                            on=["Year", "ClassCode"],
                                            how='left')
            columns = [
                'Time', 'LearningArea', 'SubjectCode', 'ClassCode',
                "TeacherCode", 'StudentCode', 'ResultName', 'ResultGrade',
                'ResultScore', 'Type'
            ]
            self.data = pd.concat([self.data, selected_df[columns]],
                                  ignore_index=True)

    def addProgressReportsExport(
            self,
            filename: str,
            compass_progress_reports_schema: list[dict],
            time: str = None,
            replace_values: dict[str, dict] = None) -> None:
        """Adds data from a Compass progress reports export."""
        try:
            temp_df = pd.read_csv(filename,
                                  na_values=None,
                                  keep_default_na=False,
                                  dtype=str)
        except EmptyDataError:
            return Reports()
        temp_df.rename(columns={
            "Id": "StudentCode",
            "Subject": "ClassCode",
            "Teacher": "TeacherCode"
        },
                       inplace=True)

        for data_set in compass_progress_reports_schema:
            # unpivot progress report items
            value_vars = [
                x for x in data_set['columns'] if x in temp_df.columns
            ]
            if len(value_vars) == 0:
                continue
            temp_df = temp_df.melt(
                id_vars=["StudentCode", "ClassCode", "TeacherCode"],
                value_vars=value_vars,
                var_name="ResultName",
                value_name="ResultGrade")

            if not time:
                time = Reports.date_from_filename(filename)
            temp_df["Time"] = time
            temp_df['Time'] = pd.to_datetime(temp_df['Time'])

            temp_df["Type"] = data_set['type']

            if replace_values:
                temp_df.replace(replace_values, inplace=True)
            results = temp_df["ResultGrade"].unique()
            for result in results:
                if result not in data_set['result_values'].keys():
                    print(
                        f"Warning: Result '{result}' not found in result_values mapping for {data_set['columns']}."
                    )
            temp_df["ResultScore"] = temp_df["ResultGrade"].map(
                data_set['result_values'])

            temp_df['Year'] = temp_df['Time'].dt.year
            temp_df = temp_df.merge(self.classes[[
                "Year", "ClassCode", "SubjectCode", "LearningArea"
            ]],
                                    on=["Year", "ClassCode"],
                                    how='left')
            columns = [
                'Time', 'LearningArea', 'SubjectCode', 'ClassCode',
                "TeacherCode", 'StudentCode', 'ResultName', 'ResultGrade',
                'ResultScore', 'Type'
            ]
            self.data = pd.concat([self.data, temp_df[columns]],
                                  ignore_index=True)

    def saveSummary(self, filename: str) -> None:
        """Aggregates results by Type to produce a summary."""
        columns = ['Time', 'LearningArea', 'StudentCode', 'ResultScore', 'Type']
        types = self.data["Type"].unique()
        (self.data[columns].groupby(
            ["Time", 'LearningArea', "StudentCode",
             "Type"]).mean().round(2).reset_index().pivot(
                 index=["Time", 'LearningArea', "StudentCode"],
                 columns=["Type"],
                 values="ResultScore").reset_index().dropna(
                     subset=types, how='all').fillna("").to_csv(filename,
                                                                index=False))

    def saveReports(self, filename: str) -> None:
        self.data.to_csv(filename, index=False)
