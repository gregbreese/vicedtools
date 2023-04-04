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
"""Executable script for creating a table of student PAT scores."""

from datetime import datetime
import glob
import json
import os

import pandas as pd

from vicedtools.acer import OARSTests, PATSittings

if __name__ == "__main__":
    from config import (oars_tests_json, pat_sittings_dir, pat_scores_csv,
                        student_details_csv)

    # import test metadata
    with open(oars_tests_json, 'r', encoding='utf-8') as fp:
        tests = json.load(fp)
    tests = OARSTests(tests)
    # import all sittings exports and combine
    filenames = glob.glob(os.path.join(pat_sittings_dir, "sittings*.json"))
    sittings = PATSittings([])
    for filename in filenames:
        print(filename)
        with open(filename, 'r', encoding='utf-8') as fp:
            temp = json.load(fp)
        sittings.extend(PATSittings(temp))
    # export summary
    df = sittings.summary(tests)

    # attempt to fix any missing year level values
    students = pd.read_csv(student_details_csv)
    students = students.loc[students["Status"] == "Active"].copy()
    students.rename(columns={"SUSSI ID": "Username"}, inplace=True)
    students['Year level value'] = students['Year Level'].str[-2:].astype(int)
    df = df.merge(students[["Username", "Year level value"]], on="Username")
    this_year = datetime.today().year
    df["Year level (calculated)"] = df["Year level value"] - (
        this_year - df["Completed"].dt.year)
    rows = df["Year level (at time of test)"] == ""
    df.loc[rows,
           "Year level (at time of test)"] = df.loc[rows,
                                                    "Year level (calculated)"]

    folder = os.path.dirname(pat_scores_csv)
    if not os.path.exists(folder):
        os.makedirs(folder)
    df.to_csv(pat_scores_csv, index=False)
