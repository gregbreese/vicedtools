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
"""Executable script for combining NAPLAN outcome exports to a single file."""

import glob
import os

import pandas as pd

if __name__ == "__main__":
    from config import (naplan_outcomes_combined_csv, naplan_outcomes_dir)

    files = glob.glob(os.path.join(naplan_outcomes_dir, "*Outcome*.csv"))
    columns = [
        "APS Year", "Reporting Test", "First Name", "Second Name", "Surname",
        "READING_nb", "WRITING_nb", "SPELLING_nb", "NUMERACY_nb",
        "GRAMMAR & PUNCTUATION_nb", "Class", "Date of Birth", "Gender", "LBOTE",
        "ATSI", "Home School Name", "Reporting School Name", "Cases ID"
    ]
    df = pd.DataFrame(columns=columns)

    for f in files:
        temp_df = pd.read_csv(f)
        if len(temp_df.columns) == 18 and temp_df.columns[0] == "APS Year":
            temp_df.columns = columns
            df = pd.concat([df, temp_df])
    df[columns].to_csv(naplan_outcomes_combined_csv, index=False)
