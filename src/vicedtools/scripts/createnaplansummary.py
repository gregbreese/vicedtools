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
"""Executable script for combining NAPLAN outcome exports to a single file."""

import glob

import numpy as np
import pandas as pd

from vicedtools.scripts.config import (naplan_outcomes_combined_csv,
                                        naplan_outcomes_most_recent_csv,
                                        naplan_outcomes_dir)


def get_band(score: str, test: str) -> int:
    if score == "":
        return np.nan
    year_level = int(test[2])
    if score < 270 and year_level == 3:
        return 1
    elif score < 322 and year_level == 3:
        return 2
    elif score < 374 and year_level <= 5:
        return 3
    elif score < 426 and year_level <= 7:
        return 4
    elif score < 478:
        return 5
    elif score < 530 or year_level == 3:
        return 6
    elif score < 582:
        return 7
    elif score < 634 or year_level == 5:
        return 8
    elif score < 686 or year_level == 7:
        return 9
    else:
        return 10


def is_in_top_two_bands(band, test):
    year_level = int(test[2])
    return ((year_level == 3 and band >= 5) or
            (year_level == 5 and band >= 7) or
            (year_level == 7 and band >= 8) or (year_level == 9 and band >= 9))


def is_in_bottom_two_bands(band, test):
    year_level = int(test[2])
    return ((year_level == 3 and band <= 2) or
            (year_level == 5 and band <= 4) or
            (year_level == 7 and band <= 5) or (year_level == 9 and band <= 6))


def main():

    filenames = glob.glob(f"{naplan_outcomes_dir}/*Outcome*.csv")
    outcomes_dfs = []
    for filename in filenames:
        temp_df = pd.read_csv(filename, dtype='str')
        outcomes_dfs.append(temp_df)

    outcomes_df = pd.concat(outcomes_dfs)
    outcomes_df.columns = [c.strip() for c in outcomes_df.columns]

    fields = [
        "READING", "WRITING", "SPELLING", "NUMERACY", "GRAMMAR & PUNCTUATION"
    ]
    for field in fields:
        # newer exports have columns like 'READING'
        # older exports have columns like 'READING_nb'
        if field in outcomes_df.columns:
            column = field
        elif f"{field}_nb" in outcomes_df.columns:
            column = f"{field}_nb"
        else:
            raise KeyError(f"'{field}' missing from Dataframe")
        outcomes_df[field] = outcomes_df[column].astype(float)
        outcomes_df[f"{field}_band"] = outcomes_df.apply(
            lambda x: get_band(x[column], x["Reporting Test"]), axis=1)
        outcomes_df[f"{field}_toptwo"] = outcomes_df.apply(
            lambda x: is_in_top_two_bands(x[column], x["Reporting Test"
                                                               ]),
            axis=1)
        outcomes_df[f"{field}_bottomtwo"] = outcomes_df.apply(
            lambda x: is_in_bottom_two_bands(x[column], x[
                "Reporting Test"]),
            axis=1)

    column_order = [
        'APS Year', 'Reporting Test', 'Cases ID', 'First Name', 'Second Name',
        'Surname', 'Gender', 'READING', 'READING_band', 'READING_toptwo',
        'READING_bottomtwo', 'WRITING', 'WRITING_band', 'WRITING_toptwo',
        'WRITING_bottomtwo', 'SPELLING', 'SPELLING_band', 'SPELLING_toptwo',
        'SPELLING_bottomtwo', 'NUMERACY', 'NUMERACY_band', 'NUMERACY_toptwo',
        'NUMERACY_bottomtwo', 'GRAMMAR & PUNCTUATION',
        'GRAMMAR & PUNCTUATION_band', 'GRAMMAR & PUNCTUATION_toptwo',
        'GRAMMAR & PUNCTUATION_bottomtwo'
    ]

    outcomes_df[column_order].to_csv(naplan_outcomes_combined_csv, index=False)
    (outcomes_df[column_order]
     .sort_values(by="APS Year", ascending=False)
     .drop_duplicates(subset="Cases ID")
     .to_csv(naplan_outcomes_most_recent_csv, index=False)
     )


if __name__ == "__main__":
    main()
