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
"""Utilities for formatting data for upload to GC."""

import pandas as pd

def create_student_details_gc_csv(compass_student_details_file: str,
                                  save_path: str) -> None:
    '''Creates a csv for uploading to GC.

    Args:
        compass_student_details: a student details export csv from Compass. Can be 
            downloaded using vicedtools.compass.export_student_details or directly
            from https://[schoolID].compass.education/Services/FileDownload/CsvRequestHandler?type=37
        save_path: the path to save the csv
    '''
    details_df = pd.read_csv(compass_student_details_file)
    details_df = details_df[details_df["Status"] == "Active"].copy()
    details_df.rename(columns={
        "SUSSI ID": "StudentCode",
        "First Name": "FirstName",
        "Preferred Name": "PrefName",
        "Last Name": "Surname",
        "Year Level": "YearLevel",
        "Form Group": "HomeGroup"
    },
                      inplace=True)
    details_df["Surname"] = details_df["Surname"].str.title()

    def year_level_number(yr_lvl_str):
        digits = yr_lvl_str[-2:]
        return int(digits)

    details_df["YearLevel"] = details_df["YearLevel"].apply(year_level_number)
    columns = [
        "StudentCode", "Surname", "FirstName", "PrefName", "Gender",
        "YearLevel", "HomeGroup"
    ]
    details_df[columns].to_csv(save_path, index=False)
