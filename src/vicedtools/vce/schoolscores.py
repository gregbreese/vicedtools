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
"""Functions for working with VCE school scores."""

import re

from bs4 import BeautifulSoup
import pandas as pd


def parse_vass_school_scores_file(file_name: str) -> pd.DataFrame:
    """Converts the data in VASS school score export into a pandas DataFrame.

    VASS school score exports contain scores in a HTML table. This function
    reads the relevant values into a DataFrame.

    Args:
        file_name: The path of the school scores export.

    Returns:
        A DataFrame containing the total score results from the VASS export.
    """
    #open file and parse HTML
    html = open(file_name).read()
    soup = BeautifulSoup(html)
    table = soup.find("table")
    #extract table data as csv
    output_rows = []
    for table_row in table.findAll('tr'):
        columns = table_row.findAll('td')
        output_row = []
        for column in columns:
            output_row.append(column.text)
        output_rows.append(output_row)
    # import results rows from CSV into dataframe
    df = pd.DataFrame(data=output_rows[7:], columns=output_rows[5])
    df.drop(columns=df.columns[4:], inplace=True)
    # drop NAs and make all scores out of 1.
    df = df[df.iloc[:, 3] != "NA"]
    mark_total_pattern = "Total GA Score / (?P<total>[0-9]+)"
    mark_total_str = df.columns[3]
    m = re.search(mark_total_pattern, mark_total_str)
    total = m.group('total')
    scores = df.iloc[:, 3].astype(int) / int(total)
    df.drop(columns=df.columns[3], inplace=True)
    df["Score"] = scores
    # add column to dataframe with year
    year_str = output_rows[0][0]
    year_pattern = "(?P<year>[0-9][0-9][0-9][0-9])"
    m = re.search(year_pattern, year_str)
    year = m.group('year')
    # add column to dataframe with subject and unit
    subject_str = output_rows[1][0]
    subject_pattern = "- (?P<subject>[A-Z():. ]+) (?P<unit>[34])"
    m = re.search(subject_pattern, subject_str)
    subject = m.group('subject')
    unit = m.group('unit')
    # add column to dataframe with assessment data type
    assessment_type_pattern = "- (?P<type>[A-Z34 -/]+)"
    assessment_type_str = output_rows[2][0]
    m = re.search(assessment_type_pattern, assessment_type_str)
    assessment_type = m.group('type')
    df["Year"] = year
    df["Subject"] = subject
    #df["Unit"] = unit
    df["Graded Assessment"] = output_rows[2][0][6:-1]

    return df
