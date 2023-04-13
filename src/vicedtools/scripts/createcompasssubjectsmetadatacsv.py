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
"""Executable script for creating a Compass metadata csv."""

import glob
import os

import pandas as pd

from vicedtools.scripts._config import (subjects_csv, subjects_dir)


def main():
    columns = ["SubjectCode", "SubjectName", "LearningArea"]
    df = pd.DataFrame(columns=columns)

    files = glob.glob(os.path.join(subjects_dir, "*.csv"))
    for file in files:
        print(f"Processing file: {file}")
        temp_df = pd.read_csv(file)
        temp_df.rename(columns={
            "facultyName": "LearningArea",
            "shortName": "SubjectName",
            "importIdentifier": "SubjectCode"
        },
                       inplace=True)
        try:
            df = pd.concat([df, temp_df[columns]])
        except KeyError:
            pass

    df.drop_duplicates(subset=["SubjectCode"], keep="last", inplace=True)
    df.to_csv(subjects_csv, index=False)


if __name__ == "__main__":
    main()
