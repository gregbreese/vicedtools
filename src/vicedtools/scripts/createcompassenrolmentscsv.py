# Copyright 2024 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Executable script for creating a Compass enrolments metadata csv."""

import glob
import os

import pandas as pd

from vicedtools.compass import Reports
from vicedtools.scripts.config import (classes_csv, enrolments_csv,
                                        enrolment_details_dir,)

def main():
    columns = [
        "f",
        "fs",
        "ii",
        "n",
        "ss",
        "yl",
        "yln",
        "id",
        "name",
        "teacherCode",
        "academicGroup",
        "Year"
    ]
    col_renaming = {"f": "FormGroup",
                    "fs": "FinishTime",
                    "ii": "StudentCode",
                    "n": "StudentName",
                    "ss": "StartTime",
                    "yl": "YearLevel",
                    "yln": "YearLevelName",
                    "name": "ClassCode",
                    "teacherCode": "TeacherCode",
                    "academicGroup": "AademicGroup"
                    }
    classes = pd.read_csv(classes_csv)

    files = glob.glob(os.path.join(enrolment_details_dir, "* enrolments.csv"))
    temp_dfs = []
    files = glob.glob(os.path.join(enrolment_details_dir, "*.csv"))
    for file in files:
        print(f"Processing file: {file}")
        temp_df = pd.read_csv(file)
        temp_df['ss'] = pd.to_datetime(temp_df['ss'])
        temp_df['fs'] = pd.to_datetime(temp_df['fs'])
        temp_df["Year"] = ((temp_df['ss'].dt.year +
                                temp_df['fs'].dt.year) / 2)
        temp_df["Year"] = round(temp_df["Year"].mean())
        try:
            temp_dfs.append(temp_df[columns])
        except KeyError:
            pass
    enrolments_df = pd.concat(temp_dfs)
    enrolments_df = enrolments_df.rename(columns=col_renaming)
    enrolments_df = enrolments_df.merge(classes[["Year", "ClassCode", "SubjectCode", "LearningArea"]], on=["Year", "ClassCode"], how='left')
    enrolments_df = enrolments_df.sort_values(by="FinishTime", ascending=False).drop_duplicates(subset=["StudentCode", "ClassCode", "Year"])
    enrolments_df.to_csv(enrolments_csv, index=False)

if __name__ == "__main__":
    main()