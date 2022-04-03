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
    from config import (root_dir, compass_folder, progress_reports_folder,
                        progress_report_cycles_json, compass_authenticator,
                        compass_school_code)

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

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    progress_reports_dir = os.path.join(compass_dir, progress_reports_folder)
    if not os.path.exists(progress_reports_dir):
        os.mkdir(progress_reports_dir)

    progress_report_cycles_file = os.path.join(compass_dir,
                                               progress_report_cycles_json)
    with open(progress_report_cycles_file, 'r', encoding='utf-8') as f:
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
