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
"""Classes for storing data from PAT group reports exported from OARS.

The class PATResults stores collated results for a particular PAT test/
test number.

The class PATResultsCollection stores PATResults and organises them by their
test/test number. Includes the ability to take a folder containing all of your
group report exports and to parse them all in one go.
"""
from __future__ import annotations

from datetime import datetime
import glob
import re

import numpy as np
import pandas as pd

# group report column headings
COL_NAMES_FRONT = [
    "Unique ID", "Family name", "Given name", "Middle names", "Username", "DOB",
    "Gender", "Completed", "Year level (current)",
    "Year level (at time of test)", "Active tags", "Inactive tags",
    "Tags (at time of test)"
]
COL_NAMES_END = ["Score", "Scale", "Stanine", "Percentile"]

RESPONSE_ORDER = ["✓", "A", "B", "C", "D", "E"]
RESPONSE_DTYPE = pd.api.types.CategoricalDtype(categories=RESPONSE_ORDER,
                                               ordered=True)


def is_group_report_file(file_location: str) -> bool:
    '''Tests whether a given xlsx file contains a PAT Group Report.
    
    Only looks for PAT Reading 5th edition and PAT Maths 4th edition.

    Args:
        file_location: The path to the group report xlsx.

    Returns:
        Whether the given xlsx is a PAT group report export.
    '''
    df = pd.read_excel(file_location,
                       nrows=1,
                       header=None,
                       usecols=[0],
                       names=["Report name"])
    report_name = df["Report name"][0]
    pattern = ("PAT (Reading 5th Edition PAT Reading Test )"
               "|(Maths 4th Edition PAT Maths Test )[0-9]+ - Group Report")
    m = re.search(pattern, report_name)
    if m:
        return True
    else:
        return False


class PATResults:
    '''A class for storing PAT group report data.
    
    Attributes:
        test: 'Reading' or 'Maths'
        number: The test number as a string. E.g. '7'
        question_scales: A dict containing the scale difficulties for each question in this
            particular test.
        results: A pandas DataFrame containing the test results.
    '''

    def __init__(self, test: str, number: str,
                 question_scales: dict[str, float], results: pd.DataFrame):
        """Initialises PATResults with the given arguments.
        
        Mostly intended for use by the provided factory methods.
        """
        self.test = test
        self.number = number
        self.question_scales = question_scales
        self.n_questions = len(question_scales)
        self.results = results

    @classmethod
    def from_group_report(cls, filename: str) -> PATResults:
        """Creates a PATResults instance from a single group report.
        
        Args:
            filename: The path to the group report xlsx.

        Returns:
            A PATResults instance.
        """
        temp_df = pd.read_excel(filename, header=None)
        test, number = group_report_metadata(temp_df)
        question_scales = extract_question_scales(temp_df)
        col_names = (COL_NAMES_FRONT + list(question_scales) + COL_NAMES_END)
        header_row_id = locate_header_row(temp_df)
        temp_df.drop(temp_df.index[:header_row_id + 1], inplace=True)
        temp_df.rename(columns={i: col_names[i] for i in range(len(col_names))},
                       inplace=True)
        temp_df["Scale"] = temp_df["Scale"].astype(float)
        temp_df['Completed'] = pd.to_datetime(temp_df['Completed'],
                                              format="%d-%m-%Y %H:%M:%S")
        return cls(test, number, question_scales, temp_df)

    def add_group_report(self, filename: str) -> None:
        """Adds the data from a group report file to this instance.

        The test (Reading/Maths) and test number must match those of the group
        report.

        Args:
            filename: The path to the group report xlsx.

        Raises:
            ValueError: Group report test and number do not match.
        """
        temp = PATResults.from_group_report(filename)
        if (self.test == temp.test) and (self.number == temp.number):
            self.results = pd.concat([self.results, temp.results],
                                     ignore_index=True)
            self.results.drop_duplicates(subset=["Username", "Completed"],
                                         inplace=True)
        else:
            raise ValueError("Group report test and number do not match.")

    def __add__(self, other: PATResults) -> PATResults:
        if (self.test == other.test) and (self.number == other.number):
            results = pd.concat([self.results, other.results],
                                ignore_index=True)
            results.drop_duplicates(subset=["Username", "Completed"],
                                    inplace=True)
            return PATResults(self.test, self.number, self.question_scales,
                              results)
        else:
            raise ValueError("test or number attributes do not match.")

    def scores(self):
        """Returns just the score data from the stored results.

        Returns:
            A pandas Dataframe containing the scores and student identification
            columns.
        """
        columns = [
            'Username', 'Gender', 'Completed', 'Year level (at time of test)',
            'Score', 'Scale'
        ]
        temp = self.results[columns].copy()
        temp["Test"] = self.test
        temp["Number"] = self.number
        return temp


def group_report_metadata(df: pd.DataFrame) -> tuple[str, str]:
    '''Extract the test and test number from the group report DataFrame.

    Looks at the top left cell and extracts the relevant test (Reading/
    Maths) and test number data.

    Args:
        df: A pandas DataFrame containing the data from a PAT group report xlsx.

    Returns:
        A tuple of (test, number), each as strings.
    '''
    report_name = df[0][0]
    pattern = (
        "PAT (?P<subject>(Reading)|(Maths))"
        "(( 5th Edition PAT Reading Test )|( 4th Edition PAT Maths Test ))"
        "(?P<number>[0-9]+) - Group Report")
    m = re.search(pattern, report_name)
    if m:
        return m.group("subject"), m.group("number")
    else:
        raise ValueError("DataFrame did not contain a valid group report.")


def extract_question_scales(df: pd.DataFrame) -> dict[str, float]:
    '''Extract question difficulties from the group report.
    
    Searches through the group report cells and finds the columns containing
    question difficulty scale scores.

    Args:
        df: A pandas DataFrame containing the data from a PAT group report xlsx.

    Returns:
        A dictionary containing each question number (str) as a key and the 
        corresponding scale score (float) as values.

    Raises:
        ValueError: DataFrame did not contain expected question scales.
    '''
    question_scales = {}
    if df[0][3] == "Question difficulty":
        current_question = 1
        offset = 12
        while not np.isnan(float(df[current_question + offset][3])):
            question_scales[str(current_question)] = float(df[current_question +
                                                              offset][3])
            current_question += 1
    # could also extract Strand info from fifth row if present
        return question_scales
    else:
        raise ValueError("DataFrame did not contain expected question scales")


def locate_header_row(df: pd.DataFrame) -> int:
    '''Identifies the row in a group report containing the column headings.

    Args:
        df: A pandas DataFrame containing the data from a PAT group report xlsx.

    Returns:
        The row number containing the column headings.

    Raises:
        ValueError: DataFrame did not contain the expected header row.
    '''
    row_id = 0
    while row_id < len(df.index):
        if df[0][row_id] == "Unique ID":
            return row_id
        row_id += 1
    raise ValueError("DataFrame did not contain the expected header row.")


class PATResultsCollection:
    '''A container for PATResults for different tests and test numbers.
    
    Attributes:
        tests: A dict with two keys, "Maths" and "Reading"
            Each key refers to another dict that contains PATResults instances
            indexed by their test number as a string.
    '''

    def __init__(self):
        """Inits an empty PATResultsCollection."""
        self.tests = {"Maths": {}, "Reading": {}}

    def add_results(self, patresults: PATResults) -> None:
        '''Adds a PATResults to the collection.
        
        Args:
            patresults: The PATResults instance to incorporate into the
                collection.
        '''
        test = patresults.test
        number = patresults.number
        if number in self.tests[test]:
            self.tests[test][number] += patresults
        else:
            self.tests[test][number] = patresults

    def get_results(self, test: str, number: str) -> pd.DataFrame:
        '''Returns the PATResults for a particular test and number.
        
        Args:
            test: "Maths" or "Reading"
            number: The test number as a string.

        Returns:
            The corresponding instance of PATResults contained in the
            collection, if one exists.
        '''
        return self.tests[test][number]

    def export_scores(self, recent: bool = False) -> pd.DataFrame:
        '''Exports all PAT scores as a single DataFrame.
        
        Args:
            recent: if true, only export each student's most recent result

        Returns:
            A pandas DataFrame containing just the score information from all
            tests.
        '''
        export_columns = [
            'Username', 'Completed', 'Year level (at time of test)', 'Test',
            'Number', 'Score', 'Scale', 'Score category'
        ]
        results_columns = [
            'Username', 'Completed', 'Year level (at time of test)', 'Score',
            'Scale'
        ]
        export = pd.DataFrame(columns=export_columns)

        for test in self.tests:
            for number in self.tests[test]:
                temp = self.tests[test][number].results[results_columns].copy()
                temp['Test'] = test
                temp['Number'] = number
                temp['Completed'] = pd.to_datetime(temp['Completed'],
                                                   format="%d-%m-%Y %H:%M:%S")
                temp['Score category'] = temp.apply(lambda x: score_categoriser(
                    test, x['Year level (at time of test)'], x['Completed'], x[
                        "Scale"]),
                                                    axis=1)

                export = pd.concat([export, temp], ignore_index=True)
        if recent:
            export.sort_values("Completed", ascending=False, inplace=True)
            export.drop_duplicates(subset=["Username", "Test"], inplace=True)
        return export

    def scores(self) -> pd.DataFrame:
        columns = [
            'Username', 'Gender', 'Completed', 'Year level (at time of test)',
            'Score', 'Scale', 'Test', 'Number'
        ]
        scores = pd.DataFrame(columns=columns)
        for test in self.tests:
            for number in self.tests[test]:
                temp = self.tests[test][number].scores()
                scores = pd.concat([scores, temp], ignore_index=True)
        return scores


def score_categoriser(test: str, year_level: str, datetime_completed: datetime,
                      score: float) -> str:
    '''Returns a qualitative description of a PAT testing result.

    Args:
        test: "Maths" or "Reading"
        year_level: "Year 5", "Year 6", "Year 7", ..., "Year 10"
            the year level of the student when they sat the test
        date: The date the test was completed.
        score: the PAT scale score the student achieved

    Returns:
        One of "Very low", "Low", "Average", "High", or "Very high".
    '''
    means = {
        'Reading': {
            1: 84.2,
            2: 101.1,
            3: 113.0,
            4: 120.9,
            5: 125.8,
            6: 128.8,
            7: 130.7,
            8: 132.6,
            9: 135.5,
            10: 140.5
        },
        'Maths': {
            1: 99.5,
            2: 108.3,
            3: 115.4,
            4: 121.1,
            5: 125.5,
            6: 128.9,
            7: 131.6,
            8: 133.6,
            9: 135.4,
            10: 137.1
        }
    }

    stdevs = {
        'Reading': {
            1: 16.3,
            2: 15.0,
            3: 15.9,
            4: 16.2,
            5: 13.2,
            6: 12.8,
            7: 13.0,
            8: 12.8,
            9: 12.4,
            10: 12.2
        },
        'Maths': {
            1: 11.4,
            2: 12.2,
            3: 13.0,
            4: 11.4,
            5: 12.6,
            6: 11.9,
            7: 13.1,
            8: 12.3,
            9: 12.9,
            10: 12.4
        }
    }
    # expect year_level as "Year 7"
    pattern = r"[A-Za-z ]*(?P<yearlevel>[0-9]+)"
    m = re.search(pattern, year_level)
    if m:
        year_level_num = int(m.group('yearlevel'))
    else:
        return ""
    if datetime_completed.month <= 4:
        year_level_num -= 1
    if year_level_num > 10:
        year_level_num = 10
    z = (score - means[test][year_level_num]) / stdevs[test][year_level_num]
    if z < -1.75:
        return "Very low"
    elif z < -0.75:
        return "Low"
    elif z < 0.75:
        return "Average"
    elif z < 1.75:
        return "High"
    else:
        return "Very high"


def group_reports_to_patresults(path: str,
                                verbose: bool = True) -> PATResultsCollection:
    '''Reads all PAT group reports in path.

    Args:
        path: The directory to search for group report files.
        verbose: If True, then print the path to each file  as it is parsed.

    Returns:
        A PATResultsCollection containg the results from all group reports in
        the directory.
    '''
    results = PATResultsCollection()
    filenames = glob.glob(path + "*.xlsx")
    for filename in filenames:
        if is_group_report_file(filename):
            print(filename)
            temp = PATResults.from_group_report(filename)
            results.add_results(temp)
    return results
