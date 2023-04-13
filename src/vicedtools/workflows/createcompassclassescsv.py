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
"""Executable script for creating a Compass classes metadata csv."""

import glob
import os

import pandas as pd

if __name__ == "__main__":
    from config import (classes_csv, class_details_dir)

    columns = [
        'facultyName', 'finish', 'importIdentifier', 'start',
        'subjectImportIdentifier', 'subjectLongName', 'yearLevelShortName',
        'managerImportIdentifier', 'Year'
    ]
    df = pd.DataFrame(columns=columns)
    files = glob.glob(os.path.join(class_details_dir, "*.csv"))
    for file in files:
        print(f"Processing file: {file}")
        temp_df = pd.read_csv(file)
        temp_df["Year"] = ((pd.to_datetime(temp_df['start']).dt.year +
                            pd.to_datetime(temp_df['start']).dt.year) / 2)
        temp_df["Year"] = round(temp_df["Year"].mean())
        try:
            df = pd.concat([df, temp_df[columns]])
        except KeyError:
            pass
    df.rename(columns={
        "facultyName": "LearningArea",
        "importIdentifier": "ClassCode",
        "subjectImportIdentifier": "SubjectCode",
        "subjectLongName": "SubjectName",
        "yearLevelShortName": "YearLevelName",
        "managerImportIdentifier": "TeacherCode"
    },
              inplace=True)
    df.to_csv(classes_csv, index=False)
