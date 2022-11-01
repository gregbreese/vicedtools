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
"""Executable script for creating an xlsx's for importing students into OARS."""

from datetime import datetime, timedelta
import json
import os

import pandas as pd

from vicedtools.acer import OARSCandidates, OARSSession

from vicedtools.workflows.config import *


def class_selector(class_string, enrolment_class_pattern):
    match = re.match(enrolment_class_pattern, class_string)
    if match:
        return match.group("class_code")
    return None


def create_oars_student_imports(
        oars_candidates_json: str, student_details_csv: str,
        enrolment_details_dir: str, enrolment_cycles: list[str],
        tag_to_keep_patterns: list[str], oars_dir: str,
        enrolment_class_pattern: str, pat_most_recent_csv: str):
    """Creates the XLSXs for importing students into OARS.
    
    :meta private:
    """
    # Identify existing students in OARS
    with open(oars_candidates_json, 'r') as f:
        candidates = json.load(f)
    candidates = OARSCandidates(candidates)
    existing_students_df = candidates.student_details_export()

    # Identify students enrolled using Comapss data
    student_details_df = pd.read_csv(student_details_csv, dtype=str)
    student_details_df = student_details_df.loc[student_details_df["Status"] ==
                                                "Active"].copy()

    student_details_df.rename(columns={
        "Last Name": "Family name",
        "Preferred Name": "Given name",
        "SUSSI ID": "Username",
        "Year Level": "Year level"
    },
                              inplace=True,
                              errors="raise")
    # column formatting
    student_details_df["Family name"] = student_details_df[
        "Family name"].str.title()
    student_details_df["Date of birth"] = pd.to_datetime(
        student_details_df["Date of birth"], format="%d/%m/%Y")
    student_details_df["Date of birth"] = student_details_df[
        "Date of birth"].dt.strftime("%d-%m-%Y")
    # select relevant columns
    columns = [
        "Family name", "Given name", "Username", "Date of birth", "Gender",
        "Year level", "Form Group"
    ]
    student_details_df = student_details_df[columns]
    # create other columns
    student_details_df["Middle names"] = ""
    student_details_df["Password"] = student_details_df["Date of birth"]
    student_details_df["Password"] = "password"  # MUST CHANGE LATER
    student_details_df["Unique ID"] = student_details_df["Username"]
    student_details_df["School year"] = datetime.today().strftime('%Y')
    student_details_df["Enrolled"] = "Enrolled"

    # create tags for class enrolments, e.g. english/eal/maths classes
    enrolment_details_df = pd.DataFrame()
    if enrolment_cycles:
        for cycle in enrolment_cycles:
            enrolment_csv = os.path.join(enrolment_details_dir,
                                         f"{cycle} enrolments.csv")
            temp_df = pd.read_csv(enrolment_csv)
            enrolment_details_df = pd.concat([enrolment_details_df, temp_df],
                                             ignore_index=True)
        enrolment_details_df['ss'] = pd.to_datetime(enrolment_details_df['ss'])
        enrolment_details_df['fs'] = pd.to_datetime(enrolment_details_df['fs'])
        enrolment_details_df['enrolment length'] = enrolment_details_df[
            'fs'] - enrolment_details_df['ss']
        enrolment_details_df = enrolment_details_df.loc[
            enrolment_details_df["enrolment length"] > timedelta(
                days=30)].copy()
        enrolment_details_df['to tag'] = enrolment_details_df['name'].apply(
            lambda x: class_selector(x, enrolment_class_pattern))
        enrolment_details_df.dropna(subset=["to tag"], inplace=True)

        enrolment_details_df[
            'Tags'] = enrolment_details_df['name'] + " " + enrolment_details_df[
                "teacherCode"] + " " + enrolment_details_df[
                    "ss"].dt.year.astype(str)
        enrolment_details_df.rename(columns={"ii": "Username"}, inplace=True)

        enrolment_tags = enrolment_details_df[["Username", "Tags"]]

    # keep certain tags
    tags_to_keep = []
    for pattern in tag_to_keep_patterns:
        for candidate in candidates:
            for tag in candidate['tags']:
                if pattern in tag['name']:
                    tags_to_keep.append({
                        "Username": candidate["username"],
                        "Tags": tag["name"]
                    })
    tags_to_keep = pd.DataFrame.from_records(tags_to_keep)

    # create tags to assign tests to students without a recent test
    pat_results_df = pd.read_csv(pat_most_recent_csv)
    today = datetime.today()
    pat_results_df["Maths Completed"] = pd.to_datetime(
        pat_results_df["Maths Completed"])
    recent_maths = pat_results_df.loc[(today - pat_results_df["Maths Completed"]
                                      ) < timedelta(days=90)]['Username']
    maths_allocations = student_details_df[["Username"]].copy()
    maths_allocations["Tags"] = "Maths adaptive"
    maths_allocations = maths_allocations.loc[~maths_allocations["Username"].
                                              isin(recent_maths)].copy()
    pat_results_df["Reading Completed"] = pd.to_datetime(
        pat_results_df["Reading Completed"])
    recent_reading = pat_results_df.loc[(
        today -
        pat_results_df["Reading Completed"]) < timedelta(days=90)]['Username']
    reading_allocations = student_details_df[["Username"]].copy()
    reading_allocations["Tags"] = "Reading adaptive"
    reading_allocations = reading_allocations.loc[
        ~reading_allocations["Username"].isin(recent_reading)].copy()

    # combine tags and assign to students
    tags = pd.concat(
        [enrolment_tags, tags_to_keep, maths_allocations, reading_allocations])
    unique_tags = tags["Tags"].unique()
    tags = tags.groupby("Username").agg({'Tags': ', '.join})
    student_details_df = student_details_df.merge(tags, on="Username")

    # remove students not enrolled
    students_to_unenrol = pd.DataFrame(
        existing_students_df[~existing_students_df["Username"].
                             isin(student_details_df["Username"])])
    students_to_unenrol["Enrolled"] = "Unenrolled"
    students_to_unenrol.drop(columns=["Tags"], inplace=True)
    students_to_unenrol = students_to_unenrol.merge(tags, on="Username")

    # add system ID for existing students
    student_details_df = student_details_df.merge(
        existing_students_df[["System ID", "Username"]],
        on="Username",
        how="left")
    student_details_df.fillna("", inplace=True)

    # save exports for existing students
    # save in batches of 500 students
    columns = [
        "System ID", "Family name", "Given name", "Middle names", "Username",
        "Password", "Date of birth", "Gender", "Tags", "Unique ID", "Enrolled",
        "Year level", "School year"
    ]
    export_df = pd.concat([student_details_df[columns], students_to_unenrol])
    export_df = export_df[columns]
    date_today = datetime.today().strftime('%Y-%m-%d')
    n_rows = 500
    update_df = export_df[export_df["System ID"] != ""].copy()
    for k, g in update_df.groupby(np.arange(len(update_df)) // n_rows):
        update_students_xlsx = os.path.join(
            oars_dir, f"{date_today} update students {(k+1)}.xlsx")
        g.to_excel(update_students_xlsx, index=False)

    # save export for new students
    new_students_xlsx = os.path.join(oars_dir, "new students to add.xlsx")
    new_student_columns = [
        "Family name", "Given name", "Middle names", "Username", "Password",
        "Date of birth", "Gender", "Tags", "Unique ID", "Year level",
        "School year"
    ]
    export_df[export_df["System ID"] == ""][new_student_columns].to_excel(
        new_students_xlsx, "Sheet1", index=False)

    # save a string with all tags to bulk create tags if necessary
    oars_tags_csv = os.path.join(oars_dir, "oars tags.csv")
    with open(oars_tags_csv, 'w') as f:
        f.write(",".join(unique_tags))


if __name__ == "__main__":
    from config import (student_details_csv, oars_candidates_json,
                        enrolment_details_dir, oars_dir, pat_most_recent_csv,
                        oars_tag_enrolment_cycles,
                        oars_tag_enrolment_class_pattern,
                        oars_tag_to_keep_patterns)

    create_oars_student_imports(oars_candidates_json, student_details_csv,
                                enrolment_details_dir,
                                oars_tag_enrolment_cycles,
                                oars_tag_to_keep_patterns, oars_dir,
                                oars_tag_enrolment_class_pattern,
                                pat_most_recent_csv)
