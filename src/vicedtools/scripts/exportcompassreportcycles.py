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
"""Executable script for exporting Compass report cycles."""

import json
import sys
import os

from vicedtools.compass.compasssession import CompassSession, CompassAuthenticator
from vicedtools.scripts._config import (report_cycles_json,
                                        compass_authenticator,
                                        compass_school_code)


def main():
    parent_dir = os.path.dirname(report_cycles_json)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    s = CompassSession(compass_school_code, compass_authenticator)
    cycles = s.get_report_cycles()
    with open(report_cycles_json, "w", encoding='utf-8') as f:
        json.dump(cycles, f)


if __name__ == "__main__":
    main()
