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
"""Classes for storing PAT sitting data."""

from __future__ import annotations

from collections import abc
from datetime import datetime
import time

import pandas as pd

from vicedtools.acer.patresults import score_categoriser
from vicedtools.acer.oarstests import OARSTests


class PATSitting(dict):
    """A class for storing a PAT sitting result."""

    def group_report(self, tests: OARSTests) -> dict:
        """Returns the data provided in a PAT group report export for this sitting."""
        data = {}
        try:
            data['Unique ID'] = self['unique_id']
        except KeyError:
            data['Unique ID'] = ""
        data['Family name'] = self['family_name']
        data['Given name'] = self['given_name']
        try:
            data['Middle names'] = self['middle_name']
        except KeyError:
            data['Middle names'] = ""
        data['Username'] = self['username']
        data['DOB'] = datetime.strptime(str(self['dob']), "%Y%m%d")
        data['Gender'] = self['gender'].title()
        data['Completed'] = datetime.strptime(
            time.ctime(self['sitting']['completed']), "%a %b %d %H:%M:%S %Y")
        data['Year level (current)'] = self['yearLevel']['current']
        data['Year level (at time of test)'] = year_level_at_time_of_test(
            self['yearLevel'], self['sitting']['updated'])
        data['Active tags'] = ""
        data['Inactive tags'] = ""
        for key, value in self['responses'].items():
            data[key] = extract_response(value)
        data['Score'] = self['score']['score']
        data['Scale'] = self['score']['scale']
        data['Stanine'] = self['score']['norms'][1]['stanine']
        data['Percentile'] = self['score']['norms'][1]['percentile']

        test_id = self['sitting']['test_id']
        form_id = self['sitting']['form_id']
        test_name = tests.get_name_from_id(test_id)
        form_name = tests.get_test_from_id(test_id).get_form_name_from_id(
            form_id)
        data['Test'] = test_name
        data['Test form'] = form_name

        return data

    def summary(self, tests: OARSTests) -> dict:
        """Extracts a summary of the results.
        
        Args:
            tests: An instance of PATTests containing the relevant test metadata.
        
        Returns:
            A dictionary containing the summary.
        """
        test_name_stub = {
            "PAT Maths 4th Edition": "Maths",
            "PAT Reading 5th Edition": "Reading",
            "PAT Maths Adaptive": "Maths",
            "PAT Reading Adaptive": "Reading",
            "eWrite": "eWrite"
        }

        data = {}
        data['Username'] = self['username']
        data['Completed'] = datetime.strptime(
            time.ctime(self['sittingTimeStamp']), "%a %b %d %H:%M:%S %Y")
        data[
            'Year level (at time of test)'] = self['yearLevel']
        data['Scale'] = self['scaleScore']
        data["Error"] = self['scaleScoreErrorMargin']
        data['Test form'] = self['formName']
        try:
            data['Test'] = test_name_stub[self['testName']]
            data['Score category'] = score_categoriser(
                data['Test'], data['Year level (at time of test)'],
                data['Completed'], data['Scale'])
        except KeyError:
            data['Test'] = self['testName']
            data["Score category"] = ""

        return data


class PATSittings(list):
    """A class for storing PAT sitting results."""

    def __init__(self, sittings: list[dict]):
        if isinstance(sittings, PATSittings):
            super().__init__(sittings)
        if isinstance(sittings, abc.Sequence):
            super().__init__([PATSitting(i) for i in sittings])
        else:
            raise TypeError(f"Unsupported type: {type(sittings)}")

    def group_report(self, tests: OARSTests, test_name: str,
                     form_name: str) -> list:
        """Extracts data for the preparation of a group report spreadsheet.
        
        Args:
            tests: A PATTests instance containing the relevant test metadata.
            test_name: The name of the test to export. E.g. "PAT Maths 4th Edition"
            form_name: The name of the form to export. E.g. "PAT Maths Test 6"
            
        Returns:
            A list of dictionaries containing the relevant columns for each sitting.
        """
        test_id = tests.get_id_from_name(test_name)
        form_id = tests.get_test_from_name(test_name).get_form_id_from_name(
            form_name)
        data = []
        for sitting in self:
            if sitting["sitting"]["test_id"] == test_id and sitting["sitting"][
                    "form_id"] == form_id:
                data.append(sitting.group_report(tests))
        return data

    def summary(self,
                tests: OARSTests,
                recent_only: bool = False) -> pd.DataFrame:
        """Extracts a basic summary of results.
        
        Args:
            tests: A PATTests instance containing the relevant test metadata.
            recent_only: If True, only give the most recent result for each student.
        
        Returns:
            A pandas DataFrame with the summary.
        """
        rows = [s.summary(tests) for s in self]
        df = pd.DataFrame.from_records(rows)
        if recent_only:
            df.sort_values("Completed", ascending=False, inplace=True)
            df.drop_duplicates(subset=["Username", "Test"], inplace=True)
        return df


def year_level_at_time_of_test(year_levels: dict, time_of_test: int) -> str:
    for yr in year_levels['history']:
        if time_of_test > yr['start']['sec'] and time_of_test < yr['end']['sec']:
            return yr['value']
    return ""


def extract_response(response: dict) -> str:
    if response['class'] == 'correct':
        return '✓'
    else:
        return response['key']
