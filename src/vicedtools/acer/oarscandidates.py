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
"""Classes for storing OARS candidate data.

Wrapper for data downloaded from https://oars.acer.edu.au/api/{school}/candidates/getCandidateIds."""

from __future__ import annotations

from collections import abc
from datetime import datetime
import time

import pandas as pd


class OARSCandidates(list):
    """A class for storing metadata for OARS candidates."""

    def __init__(self, candidates: list[dict]):
        if isinstance(candidates, OARSCandidates):
            return candidates
        if isinstance(candidates, abc.Sequence):
            super().__init__([OARSCandidate(i) for i in candidates])
        else:
            raise TypeError(f"Unsupported type: {type(candidates)}")

    def student_details_export(self,
                               include_sittings: bool = False) -> pd.DataFrame:
        """Extracts the student details data export from the candidates.
        
        Columns match the export provided by OARS.
        
        Args:
            include_tests: If true, adds an additional column listing any incomplete sittings.
        
        Returns:
            A pandas DataFrame with the student details table.
        """
        rows = [c.student_details_export(include_sittings) for c in self]
        data = pd.DataFrame.from_records(rows)
        return data

    def sitting_status_export(self) -> pd.DataFrame:
        """Extracts the sitting information from the candiates.
        
        Provides the completion status of all assigned sittings.
        
        Returns:
            A pandas DataFrame with the sitting details.
        """
        rows = []
        for sitting in self:
            rows += sitting.get_sitting_status()
        data = pd.DataFrame.from_records(rows)
        return data


class OARSCandidate(dict):
    """A class for storing metadata for an OARS candidate."""

    def __init__(self, item):
        super().__init__(item)

    def student_details_export(self, include_sittings: bool = False):
        row = {}
        row["System ID"] = self['id']
        row["Family name"] = self['family_name']
        row["Given name"] = self['given_name']
        try:
            row["Middle names"] = self['middle_name']
        except KeyError:
            row["Middle names"] = ""
        row["Username"] = self['username']
        row["Password"] = self['plaintext_password']
        row["Date of birth"] = self['dobString']
        row["Gender"] = self['gender'].title()
        row["Tags"] = ",".join([t['name'] for t in self['tags']])
        row['Unique ID'] = self['unique_id']
        if self["enrolled"] == 1:
            row["Enrolled"] = 'enrolled'
        elif self['enrolled'] == 0:
            row["Enrolled"] = 'unenrolled'
        else:
            row['enrolled'] = 'pre-enrolled'
        row["Year level"] = self['year']
        row["School year"] = self['currentSchoolYearLabel']
        if include_sittings:
            incomplete = []
            for sitting in self['sittings']:
                if not sitting["completed"]:
                    incomplete.append(
                        f"{sitting['test_name']} {sitting['form_name']}")
            row["Incomplete tests"] = ",".join(incomplete)
        return row

    def get_sitting_status(self):
        rows = []
        for sitting in self['sittings']:
            row = {}
            row["System ID"] = self['id']
            row["Family name"] = self['family_name']
            row["Given name"] = self['given_name']
            row["Username"] = self['username']
            row["Tests"] = sitting['test_name']
            row["Form"] = sitting['form_name']
            row["Assigned date"] = datetime.strptime(
                time.ctime(sitting['created']),
                "%a %b %d %H:%M:%S %Y").strftime("%d-%m-%Y")
            if sitting["completed"]:
                row["Status"] = "Completed"
                row["Completed date"] = datetime.strptime(
                    time.ctime(sitting['created']),
                    "%a %b %d %H:%M:%S %Y").strftime("%d-%m-%Y")
            else:
                row["Status"] = "Incomplete"
                row["Completed date"] = ""
            rows.append(row)
        return rows
