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
"""Executable script for exporting Compass Learning Task data."""

import argparse
import json
import os
import sys

from vicedtools.compass import CompassSession, sanitise_filename

if __name__ == "__main__":
    from config import (root_dir, compass_folder, learning_tasks_folder,
                        compass_authenticator, compass_school_code,
                        academic_groups_json)

    parser = argparse.ArgumentParser(
        description='Export all Compass learning tasks.')
    parser.add_argument('--forceall',
                        '-a',
                        action="store_true",
                        help='force re-download existing learning task exports')
    parser.add_argument('--forcecurrent',
                        '-c',
                        action="store_true",
                        help='force re-download current academic cycle')
    args = parser.parse_args()

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    learning_tasks_dir = os.path.join(compass_dir, learning_tasks_folder)
    if not os.path.exists(learning_tasks_dir):
        os.mkdir(learning_tasks_dir)

    academic_groups_file = os.path.join(compass_dir, academic_groups_json)
    with open(academic_groups_file, 'r', encoding='utf-8') as f:
        cycles = json.load(f)

    s = CompassSession(compass_school_code, compass_authenticator)

    for cycle in cycles:
        sanitised_name = sanitise_filename(cycle['name'])
        file_name = os.path.join(learning_tasks_dir,
                                 f"LearningTasks-{sanitised_name}.csv")
        if not os.path.exists(file_name) or args.forceall or (
                args.forcecurrent and cycle['isRelevant']):
            print(f"Exporting {cycle['name']}")
            s.export_learning_tasks(cycle['id'],
                                    cycle['name'],
                                    save_dir=learning_tasks_dir)
