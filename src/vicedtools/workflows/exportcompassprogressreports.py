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
"""Executable script for exporting all Compass progress reports."""

import argparse
import json
import os

from vicedtools.compass import CompassSession, sanitise_filename

if __name__ == "__main__":
    from config import (progress_reports_dir, progress_report_cycles_json,
                        compass_authenticator, compass_school_code)

    parser = argparse.ArgumentParser(
        description='Export all Compass progress reports.')
    parser.add_argument('--forceall',
                        '-a',
                        action="store_true",
                        help='force re-download existing reports')
    parser.add_argument('--forcerecent',
                        '-r',
                        action="store_true",
                        help='force re-download most recent report')
    args = parser.parse_args()

    if not os.path.exists(progress_reports_dir):
        os.makedirs(progress_reports_dir)

    with open(progress_report_cycles_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)

    s = CompassSession(compass_school_code, compass_authenticator)

    for i in range(len(cycles)):
        cycle = cycles[i]
        sanitised_title = sanitise_filename(cycle['title'])
        file_name = os.path.join(progress_reports_dir, f"{sanitised_title}.csv")
        if not os.path.exists(file_name) or args.forceall or (args.forcerecent
                                                              and i == 0):
            print(f"Exporting {cycle['title']}")
            s.export_progress_reports(cycle['id'], cycle['title'],
                                      progress_reports_dir)
