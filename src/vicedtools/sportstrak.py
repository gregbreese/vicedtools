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
"""Functions for creating import spreadsheets for Sportstrak."""

import re

import pandas as pd


def create_sportstrak_student_import(student_details_csv: str, 
                                     destination_xlsx: str, 
                                     house_map: dict[str, str] = {}) -> None:
    """Creates a student import spreadsheet for SportsTrak.

    Args:
        student_details_csv: A student details export from Compass, such as from 
            https://gwsc-vic.compass.education/Services/FileDownload/CsvRequestHandler?type=37
            or vicedtools.compass.export_student_details
        house_map: Optional, a dictionary for renaming houses.
        destination_xlsx: The filename to save the Excel file as.
    """
    df = pd.read_csv(student_details_csv)

    df = df[df["Status"] == "Active"]
    df["House"] = df["House"].replace(house_map)
    df["Middle Name"] = ""
    df["Year Level"] = df["Year Level"].str[5:]
    df["Gender"] = df["Gender"].str[0]
    df["Date of birth"] = pd.to_datetime(df["Date of birth"], format="%d/%m/%Y")
    columns = ["SUSSI ID", "Last Name", "Preferred Name","Middle Name", 
               "Date of birth", "Gender", "House", "Year Level"]
    df = df[columns]

    writer = pd.ExcelWriter(destination_xlsx,  datetime_format='DD/MM/YYYY')
    df.to_excel(writer, "Sheet1", index=False)
    writer.close()