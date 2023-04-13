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
"""Executable script for exporting Compass progress report data."""

import json
import os
import sys

from vicedtools.compass import CompassSession
from vicedtools.scripts._config import (progress_reports_dir,
                                        progress_report_cycles_json,
                                        compass_authenticator,
                                        compass_school_code)


def main():
    if len(sys.argv) != 2:
        print("Received arguments were: ", sys.argv[1:])
        print('Requires one argument: cycle')
        sys.exit(2)
    cycle_title = sys.argv[1]

    if not os.path.exists(progress_reports_dir):
        os.makedirs(progress_reports_dir)

    with open(progress_report_cycles_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)
    cycle_id = None
    for c in cycles:
        if c['title'] == cycle_title:
            cycle_id = c['id']
            break
    if cycle_id:
        s = CompassSession(compass_school_code, compass_authenticator)
        s.export_progress_reports(cycle_id, cycle_title, progress_reports_dir)
        sys.exit(0)
    else:
        print("Progress report cycle not found.")
        sys.exit(2)


if __name__ == "__main__":
    main()
