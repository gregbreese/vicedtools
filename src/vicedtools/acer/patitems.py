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
"""Classes for storing PAT item metadata.

Wrapper for data downloaded from https://oars.acer.edu.au/api/{self.school}/reports-new/getGroupReportItemsData/.
"""

from __future__ import annotations

from collections import abc


class PATItems(list):
    """A class for storing metadata for PAT items."""

    def __init__(self, items: list[dict]):
        if isinstance(items, PATItems):
            super().__init__(items)
        if isinstance(items, abc.Sequence):
            super().__init__([PATItem(i) for i in items])
        else:
            raise TypeError(f"Unsupported type: {type(items)}")

    def group_report_key(self):
        """Returns data for the group report for this test."""
        data = [x.group_report_key() for x in self]
        return data


class PATItem(dict):
    """A class for storing metadata for a PAT item."""

    def __init__(self, item):
        super().__init__(item)

    def group_report_key(self):
        """Returns data for the group report key for this item."""
        data = {}
        data['Question number'] = self['position']
        data['Percentage correct'] = 0
        data['Strand'] = self['classification']
        data['Question difficulty'] = self['difficulty']
        return data
