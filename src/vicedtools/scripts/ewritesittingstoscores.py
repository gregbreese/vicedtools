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
"""Executable script for creating a table of student eWrite scores."""

import glob
import json
import os
import sys

import pandas as pd

from vicedtools.acer import OARSTests, EWriteSittings
from vicedtools.scripts._config import (oars_tests_json, ewrite_sittings_dir,
                                        ewrite_scores_csv, ewrite_criteria_csv)


def main():
    # import test metadata
    with open(oars_tests_json, 'r', encoding='utf-8') as fp:
        tests = json.load(fp)
    tests = OARSTests(tests)

    # import all settings exports and combine
    sittings_files = glob.glob(
        os.path.join(ewrite_sittings_dir, "sittings*.json"))
    sittings = []
    for f in sittings_files:
        with open(f, 'r', encoding='utf-8') as f:
            new_sittings = json.load(f)
        sittings += new_sittings
    if not sittings:
        print("No sittings found.")
        sys.exit(0)
    sittings = EWriteSittings(sittings)
    # remove duplicates, rename columns
    sittings_df = pd.DataFrame.from_records(sittings.group_report(tests))
    sittings_df.drop_duplicates(subset=["Date", "Username"], inplace=True)
    sittings_df.rename(columns={
        "Username": "StudentCode",
        'Year level (at time of test)': 'Year level'
    },
                       inplace=True)
    sittings_df["Date"] = pd.to_datetime(sittings_df["Date"], format="%d-%m-%Y")
    sittings_df["Score"] = sittings_df["Score"].astype('Int64').astype(
        str).replace("<NA>", "")
    sittings_df["Band"] = sittings_df["Band"].astype('Int64').astype(
        str).replace("<NA>", "")
    sittings_df["Scale"] = sittings_df["Scale"].astype('Int64').astype(
        str).replace("<NA>", "")

    # if student did test at beginning of year then count as previous year's year level
    def effective_year_level(year_level, date):
        year_level_num = int(year_level)
        if date.month <= 4:
            year_level_num -= 1
        return str(year_level_num)

    sittings_df['Effective year level'] = sittings_df.apply(
        lambda x: effective_year_level(x['Year level'], x["Date"]), axis=1)

    # Create overall scores table
    columns_to_save = [
        'Date', 'StudentCode', 'Year level', 'Effective year level',
        'Result flag', 'Score', 'Scale', 'Band', 'Response'
    ]
    sittings_df[columns_to_save].to_csv(ewrite_scores_csv, index=False)

    # Create criteria score table
    cols = [
        'Date', 'StudentCode', 'Year level', 'Effective year level', 'OE', 'TS',
        'ID', 'VOC', 'PARA', 'SENT', 'SPUNC', 'PINS', 'SP'
    ]
    rows = sittings_df["Result flag"] == "OK"
    criteria_df = sittings_df.loc[rows, cols].melt(
        id_vars=['Date', 'StudentCode', 'Year level', 'Effective year level'],
        value_vars=[
            'OE', 'TS', 'ID', 'VOC', 'PARA', 'SENT', 'SPUNC', 'PINS', 'SP'
        ],
        value_name="Score",
        var_name="Criteria")
    criteria_df.dropna(subset=["Score"], inplace=True)
    criteria_df["Score"] = criteria_df["Score"].astype(int)
    # merge in scale score for each criteria score
    criteria_scale_scores = tests.ewrite_criteria_scores()
    criteria_df = criteria_df.merge(criteria_scale_scores,
                                    on=["Criteria", "Score"])
    criteria_df["Scale"] = criteria_df["Scale"].replace("N/A",
                                                        "nan").astype(float)
    criteria_df.to_csv(ewrite_criteria_csv, index=False)


if __name__ == "__main__":
    main()
