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
"""Classes for storing eWrite sitting data."""

from __future__ import annotations

from collections import abc
from datetime import datetime
import time

from vicedtools.acer.oarstests import OARSTests


class EWriteSittings(list):
    """A class for storing eWrite sitting results."""

    def __init__(self, sittings: list[dict]):
        if isinstance(sittings, EWriteSittings):
            super().__init__(sittings)
        if isinstance(sittings, abc.Sequence):
            super().__init__([EWriteSitting(i) for i in sittings])
        else:
            raise TypeError(f"Unsupported type: {type(sittings)}")

    def group_report(self, tests: OARSTests) -> list:
        """Extracts data for the preparation of a group report spreadsheet.
        
        Args:
            tests: A OARSTests instance containing the relevant test metadata.
            test_name: The name of the test to export. E.g. "eWrite"
            form_name: The name of the form to export. E.g. "Task C Report (Years 5-8)"
            
        Returns:
            A list of dictionaries containing the relevant columns for each sitting.
        """
        data = []
        for sitting in self:
            if 'completed' in sitting:
                data.append(sitting.group_report(tests))
        return data


class EWriteSitting(dict):
    """A class for storing a eWrite sitting result."""

    def group_report(self, tests: OARSTests) -> dict:
        """Returns the data provided in a eWrite group report export for this sitting."""
        data = {}
        data['Display name'] = self['user']['display_name']
        data['Family name'] = self['user']['family_name']
        data['Given name'] = self['user']['given_name']
        data['Middle name'] = self['user']['middle_name']
        data['Username'] = self['user']['username']
        data['Gender'] = self['user']['gender'].title()
        data['Year level (at time of test)'] = self['user']['yearLevel']
        data['Tags'] = ",".join([t['name'] for t in self['user']['tags']])
        data['Date'] = datetime.strptime(time.ctime(self['completed']),
                                         "%a %b %d %H:%M:%S %Y")
        if 'vantageResult' in self['responses'][1]:
            data['Result flag'] = self['responses'][1]['vantageResult']['flagged_code']
        else:
            data['Result flag'] = self['responses'][1]['scoreReason']
        
        if data['Result flag'] == "OK":
            data['Score'] = self['responses'][1]['score']

            test = tests.get_test_from_id(self['test_id'])
            form = test.get_form_from_id(self['form_id'])
            scale, band = form['scaleScores'][data['Score']].values()
            data['Scale'] = scale
            data['Band'] = band
            for idx, key in enumerate([
                    'OE', 'TS', 'ID', 'VOC', 'PARA', 'SENT', 'SPUNC', 'PINS',
                    'SP'
            ]):
                data[key] = self['responses'][1]['vantageResult'][
                    'dimensionalScores'][idx]
        else:
            data['Score'] = None
            data['Scale'] = None
            data['Band'] = None
            for key in [
                    'OE', 'TS', 'ID', 'VOC', 'PARA', 'SENT', 'SPUNC', 'PINS',
                    'SP'
            ]:
                data[key] = None

        if 'response' in self['responses'][1]:
            data['Response'] = self['responses'][1]['response'][0]
        else:
            data['Response'] = ""

        return data
