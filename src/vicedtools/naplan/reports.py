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
"""Functions for creating reports from NAPLAN data"""

import pandas as pd
import glob

def get_band(score: float, test: str) -> int:
    """Returns the NAPLAN band for a given test score.
    
    Args:
        score: The naplan scale score as a float as given in the READING_nb,
        WRITING_nb, etc fields of the NAPLAN outcomes csv.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        The NAPLAN band as an integer.
    """
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

def is_in_top_two_bands(band: int, test: str) -> bool:
    """Returns True if the given band is in the top two bands for a given test.
    
    Args:
        band: The NAPLAN band as an integer.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        True if the given band is in the top two bands. 
    """
    year_level = int(test[2])
    return ((year_level == 3 and band >= 5) 
            or (year_level == 5 and band >= 7)
            or (year_level == 7 and band >= 8)
            or (year_level == 9 and band >= 9)
           )

def is_in_bottom_two_bands(band, test):
    """Returns True if the band is in the bottom two bands for a given test.
    
    Args:
        band: The NAPLAN band as an integer.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        True if the given band is in the bottom two bands.
    """
    year_level = int(test[2])
    return ((year_level == 3 and band <= 2) 
            or (year_level == 5 and band <= 4)
            or (year_level == 7 and band <= 5)
            or (year_level == 9 and band <= 6)
           )

def create_outcome_summary(naplan_outcomes_dir: str, naplan_outcomes_combined_csv: str):
    """Combines NAPLAN outcomes exports into a single summary.
    
    Combines all outcomes CSV exports from a given directory into a single
    file. Expects outcomes exports to include "Outcome" in their file name.
    Adds additional columns with the student's band for each test and
    whether the student's result was in the top two or bottom two bands.

    Args:
        naplan_outcomes_dir: The folder to search for CSV files.
        naplan_outcomes_combined_csv: The path to save the summary to.
    """
    filenames = glob.glob(f"{naplan_outcomes_dir}/*Outcome*.csv")
    outcomes_dfs = []
    for filename in filenames:
        temp_df = pd.read_csv(filename, dtype='str')
        outcomes_dfs.append(temp_df)
        
    outcomes_df = pd.concat(outcomes_dfs)
    outcomes_df.columns = [c.strip() for c in outcomes_df.columns]

    fields = ["READING", "WRITING", "SPELLING", "NUMERACY", "GRAMMAR & PUNCTUATION"]
    for field in fields:
        outcomes_df[f"{field}_nb"] = outcomes_df[f"{field}_nb"].astype(float)
        outcomes_df[f"{field}_band"] = outcomes_df.apply(lambda x: get_band(x[f"{field}_nb"], x["Reporting Test"]), axis=1)
        outcomes_df[f"{field}_toptwo"] = outcomes_df.apply(lambda x: is_in_top_two_bands(x[f"{field}_band"], x["Reporting Test"]), axis=1)
        outcomes_df[f"{field}_bottomtwo"] = outcomes_df.apply(lambda x: is_in_bottom_two_bands(x[f"{field}_band"], x["Reporting Test"]), axis=1)

    column_order = ['APS Year', 'Reporting Test', 'Cases ID', 'First Name', 'Second Name', 'Surname',
        'READING_nb', 'READING_band', 'READING_toptwo', 'READING_bottomtwo',
            'WRITING_nb', 'WRITING_band', 'WRITING_toptwo', 'WRITING_bottomtwo', 
            'SPELLING_nb', 'SPELLING_band', 'SPELLING_toptwo', 'SPELLING_bottomtwo', 
            'NUMERACY_nb', 'NUMERACY_band', 'NUMERACY_toptwo', 'NUMERACY_bottomtwo',
            'GRAMMAR & PUNCTUATION_nb', 'GRAMMAR & PUNCTUATION_band','GRAMMAR & PUNCTUATION_toptwo', 'GRAMMAR & PUNCTUATION_bottomtwo'
        ]

    outcomes_df[column_order].to_csv(naplan_outcomes_combined_csv)
