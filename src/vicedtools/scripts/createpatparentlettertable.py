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
"""Executable script for creating an xlsx for mailmerging a parent letter with PAT results."""

import datetime
import os

import pandas as pd

from vicedtools.scripts.config import (student_details_csv,
                                        student_household_information_csv,
                                        pat_scores_csv)


def main():
    student_details = pd.read_csv(student_details_csv)
    household_information = pd.read_csv(student_household_information_csv)
    pat_scores = pd.read_csv(pat_scores_csv)

    student_details.rename(columns={"SUSSI ID": "StudentCode"}, inplace=True)
    student_details_columns = [
        "StudentCode", "Preferred Name", "Last Name", "Year Level"
    ]
    student_details = student_details[student_details_columns]
    student_details["Last Name"] = student_details["Last Name"].str.title()

    household_information.rename(columns={"Student SUSSI ID": "StudentCode"},
                                 inplace=True)
    household_information_columns = [
        "StudentCode", "HouseHoldTitle", "Adult 1 Email"
    ]
    household_information = household_information[household_information_columns]

    pat_scores.rename(columns={"Username": "StudentCode"}, inplace=True)
    pat_scores["Completed"] = pd.to_datetime(pat_scores["Completed"])
    # only scores from past 6 months
    pat_scores = pat_scores.loc[pat_scores["Completed"] + datetime.timedelta(
        weeks=26) > datetime.datetime.today()]

    # get only most recent result for each test
    pat_scores.sort_values("Completed", ascending=False, inplace=True)
    pat_scores.drop_duplicates(subset=["StudentCode", "Test"], inplace=True)

    pat_score_columns = ["StudentCode", "Completed", "Test", "Score category"]
    pat_scores = pat_scores[pat_score_columns]

    naplan_goal = {
        "Very low": "At National Standard",
        "Low": "Above National Standard",
        "Average": "Above National Standard",
        "High": "Well Above National Standard",
        "Very high": "Well Above National Standard"
    }
    pat_scores["NAPLAN goal"] = pat_scores["Score category"].replace(
        naplan_goal)

    category_rename = {
        "Very low": "Well below expected level",
        "Low": "Below expected level",
        "Average": "At expected level",
        "High": "Above expected level",
        "Very high": "Well above expected level"
    }
    pat_scores["Score category"].replace(category_rename, inplace=True)

    pat_scores_wide = pat_scores.pivot(index="StudentCode", columns="Test")
    pat_scores_wide.columns = [f"{b} {a}" for (a, b) in pat_scores_wide.columns]
    pat_scores_wide.reset_index(inplace=True)

    merged = pd.merge(student_details, household_information, on="StudentCode")
    merged = pd.merge(merged, pat_scores_wide, on="StudentCode")

    # fill missing values
    for col in ["Maths Completed", "Reading Completed"]:
        merged[col].fillna("No test completed", inplace=True)
    for col in [
            "Maths Score category", "Reading Score category",
            "Maths NAPLAN goal", "Reading NAPLAN goal"
    ]:
        merged[col].fillna("N/a", inplace=True)

    save_path = os.path.join(os.path.dirname(pat_scores_csv),
                             "parent letter mail merge.csv")
    merged.to_csv(save_path, index=False)


if __name__ == "__main__":
    main()
