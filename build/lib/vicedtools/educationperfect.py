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
"""Functions for creating import spreadsheets for Education Perfect."""

import re

import pandas as pd

def import_spreadsheet(student_details_file: str,
                       student_enrolment_file: str,
                       teacher_roster_file: str,
                       email_domain: str,
                       class_regex: str,
                       destination_file: str) -> None:
    """Creates a student import spreadsheet for Education Perfect.

    Args:
        student_details_file: A student details export from Compass, such as from 
            https://gwsc-vic.compass.education/Services/FileDownload/CsvRequestHandler?type=37
            or vicedtools.compass.export_student_details
        student_enrolment_file: A student enrolment export from Compass' SDS
            export, such as from vicedtools.compass.sds_export
        teacher_roster_file: A student enrolment export from Compass' SDS
            export, such as from vicedtools.compass.sds_export
        email_domain: The school's email domain for appending to their student
            ID to create their email address. Should include leading '@'.
        class_regex: A regex expression that matches all of the desired classes.
        destination_file: The filename to save the csv file as.
    """

    student_details_df = pd.read_csv(student_details_file, dtype=str)

    columns = ["Last Name", "Preferred Name", "SUSSI ID"]
    student_details_df = student_details_df[columns]
    student_details_df.rename(columns={"Last Name":"Surname", "Preferred Name":"First Name","SUSSI ID":"Student ID"}, inplace=True, errors="raise")
    student_details_df["Student Email Address"] = student_details_df["Student ID"] + email_domain
    student_details_df["Surname"] = student_details_df["Surname"].str.title()

    # get class details and create class tags
    def class_selector(class_string):
        match = re.match(class_regex,  class_string)
        if match:
            class_code = match.group()
            return class_code
        # else
        return None
    student_enrolment_df = pd.read_csv(student_enrolment_file)
    student_enrolment_df["Class Name"] = student_enrolment_df["Section SIS ID"].apply(class_selector)
    student_enrolment_df.dropna(subset=["Class Name"],  inplace=True)
    student_enrolment_df.rename(columns={"SIS ID":"Student ID"}, inplace=True)

    # add teacher IDs
    teacher_roster_df = pd.read_csv(teacher_roster_file)
    teacher_roster_df.rename(columns={"SIS ID":"Teacher ID"}, inplace=True)
    student_enrolment_df = student_enrolment_df.merge(teacher_roster_df, on="Section SIS ID")

    # merge with student details and enrolments
    student_enrolment_df = student_details_df.merge(student_enrolment_df[["Student ID","Class Name", "Teacher ID"]], on="Student ID")

    student_enrolment_df.to_csv(destination_file,  index=False)
                                