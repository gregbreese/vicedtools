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
"""Executable script for exporting Compass progress report data."""

import json
import os
import sys

from vicedtools.compass import CompassSession

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Received arguments were: ", sys.argv[1:])
        print('Requires one argument: cycle')
        sys.exit(2)
    cycle_title = sys.argv[1]

    from config import (root_dir, compass_folder, progress_reports_folder,
                        progress_report_cycles_json, compass_authenticator,
                        compass_school_code)

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
