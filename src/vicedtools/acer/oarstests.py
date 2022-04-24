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
"""Classes for storing OARS test metadata.

Wrapper for data downloaded from https://oars.acer.edu.au/api/{school}/reports-new/getTests/.
"""

from __future__ import annotations

from collections import abc

import pandas as pd


class OARSTests(list):
    """A class for storing metadata for OARS tests."""

    def __init__(self, tests: list[dict]):
        if isinstance(tests, OARSTests):
            super().__init__(tests)
        if isinstance(tests, abc.Sequence):
            super().__init__([OARSTest(i) for i in tests])
        else:
            raise TypeError(f"Unsupported type: {type(tests)}")

    def get_test_from_id(self, test_id: str) -> OARSTest:
        """Gets a test's metadata.
        
        Args:
            test_id: The testId of the test to locate.
            
        Returns:
            A OARSTest containing metadata about the particular test.
        """
        for t in self:
            if t['testId'] == test_id:
                return t
        raise TestNotFoundError()

    def get_test_from_name(self, test_name: str) -> OARSTest:
        """Gets a test's metadata.
        
        Args:
            test_name: The name of the test to locate. 
                E.g. "PAT Maths 4th Edition"
            
        Returns:
            An OARSTest containing metadata about the particular test
        """
        for t in self:
            if t['name'] == test_name:
                return t
        raise TestNotFoundError()

    def get_id_from_name(self, test_name: str) -> str:
        """Gets a test's id from its name.
        
        Args:
            test_name: The name of the test to locate. 
                E.g "PAT Maths 4th Edition"
            
        Returns:
            The id string for the test.
        """
        for t in self:
            if t['name'] == test_name:
                return t['testId']
        raise TestNotFoundError()

    def get_name_from_id(self, test_id: str) -> str:
        """Gets a test's name from its id.
        
        Args:
            test_id: The id of the test to locate. 
            
        Returns:
            The name ofr the test. E.g "PAT Maths 4th Edition"
        """
        for t in self:
            if t['id'] == test_id:
                return t['name']
        raise TestNotFoundError()

    def ewrite_criteria_scores(self):
        """Returns a lookup table for scale scores for each eWrite criteria.

        Returns:
            A pandas DataFrame with columns 'Criteria', 'Scores', and 'Scale'.
        """
        criteria_scores = []
        ewrite_test = self.get_test_from_name('eWrite')
        categories = ewrite_test['metadata']['categories']
        for _, category_metadata in categories.items():
            for idx, score_metadata in enumerate(category_metadata['scales']):
                criteria_scores.append({
                    'Criteria': category_metadata['short_name'],
                    'Score': idx,
                    'Scale': score_metadata['scale']
                })
        return pd.DataFrame.from_records(criteria_scores)


class OARSTest(dict):
    """A class for storing metadata for a test on OARS."""

    def __init__(self, test):
        super().__init__(test)

    def get_form_id_from_name(self, form_name: str) -> str:
        """Gets a form's id from its name.
        
        Args:
            form_name: The name of the form. E.g. "PAT Maths Test 6"
            
        Returns:
            The id of the form.
        """
        for f in self['forms']:
            if f["name"] == form_name:
                return f["formId"]
        raise FormNotFoundError()

    def get_form_name_from_id(self, form_id: str) -> str:
        """Gets a form's name from it's id.
        
        Args:
            form_id: The id of the form
            
        Returns:
            The name of the form. E.g. "PAT Maths Test 6"
        """
        for f in self['forms']:
            if f["id"] == form_id:
                return f["name"]
        raise FormNotFoundError()

    def get_form_from_id(self, form_id: str) -> dict:
        """Gets a form from it's id.
        
        Args:
            form_id: The id of the form
            
        Returns:
            The the form metadata in a dictionary
        """
        for f in self['forms']:
            if f["id"] == form_id:
                return f
        raise FormNotFoundError()


class TestNotFoundError(Exception):
    """Raised if an OARS test id or name is not found."""
    pass


class FormNotFoundError(Exception):
    """Raised if an OARS form id or name is not found."""
    pass
